"""
Rate Limiter Service
Manages API rate limits across multiple data sources with intelligent queuing and caching.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from collections import deque
from dataclasses import dataclass, field
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration for an API"""
    name: str
    max_calls: int
    time_window: int  # seconds
    calls: deque = field(default_factory=deque)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)

    def can_make_call(self) -> bool:
        """Check if we can make a call within rate limits"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)

        # Remove old calls
        while self.calls and self.calls[0] < cutoff:
            self.calls.popleft()

        return len(self.calls) < self.max_calls

    def record_call(self):
        """Record that a call was made"""
        self.calls.append(datetime.now())

    def time_until_available(self) -> float:
        """Get seconds until next call is available"""
        if self.can_make_call():
            return 0

        if not self.calls:
            return 0

        oldest_call = self.calls[0]
        cutoff = datetime.now() - timedelta(seconds=self.time_window)

        if oldest_call < cutoff:
            return 0

        return (oldest_call + timedelta(seconds=self.time_window) - datetime.now()).total_seconds()


class RateLimiterService:
    """Central rate limiting service with intelligent request queuing"""

    def __init__(self):
        # API rate limits
        self.limits: Dict[str, RateLimit] = {
            # Alpha Vantage: 25 calls/day, 5 calls/minute
            'alpha_vantage_daily': RateLimit('alpha_vantage_daily', 25, 86400),  # 24 hours
            'alpha_vantage_minute': RateLimit('alpha_vantage_minute', 5, 60),

            # Yahoo Finance: No official limit, but respect ~2000/hour
            'yahoo_finance': RateLimit('yahoo_finance', 2000, 3600),

            # Tavily API: Based on tier (default 1000/month)
            'tavily_monthly': RateLimit('tavily_monthly', 1000, 2592000),  # 30 days
            'tavily_minute': RateLimit('tavily_minute', 60, 60),

            # OpenAI: Based on tier
            'openai_minute': RateLimit('openai_minute', 500, 60),
            'openai_daily': RateLimit('openai_daily', 10000, 86400),
        }

        # Request priorities (higher = more important)
        self.priorities = {
            'real_time_price': 100,  # Live price updates
            'fundamental_data': 80,   # Fundamental analysis
            'technical_indicator': 70, # Technical indicators
            'news_sentiment': 60,      # News and sentiment
            'historical_data': 50,     # Historical analysis
            'bulk_request': 30         # Batch/background jobs
        }

        # Cache for API responses
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttls = {
            'stock_price': 60,           # 1 minute for prices
            'fundamental': 21600,        # 6 hours for fundamentals
            'technical': 900,            # 15 minutes for technical
            'news': 1800,                # 30 minutes for news
            'historical': 86400          # 24 hours for historical
        }

        # Statistics
        self.stats = {
            'total_requests': 0,
            'cached_responses': 0,
            'queued_requests': 0,
            'rate_limited': 0,
            'api_calls': {}
        }

    async def execute_with_limit(
        self,
        api_name: str,
        func: Callable,
        cache_key: Optional[str] = None,
        cache_type: str = 'default',
        priority: str = 'bulk_request',
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an API call with rate limiting and caching

        Args:
            api_name: Name of the API rate limit to use
            func: Async function to execute
            cache_key: Unique key for caching (None = no cache)
            cache_type: Type of data for cache TTL
            priority: Request priority level
            *args, **kwargs: Arguments to pass to func

        Returns:
            API response
        """
        self.stats['total_requests'] += 1

        # Check cache first
        if cache_key and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() < cache_entry['expires']:
                self.stats['cached_responses'] += 1
                logger.info(f"Cache hit for {cache_key}")
                return cache_entry['data']
            else:
                # Remove expired entry
                del self.cache[cache_key]

        # Check if API limit exists
        if api_name not in self.limits:
            logger.warning(f"Unknown API: {api_name}, executing without limit")
            result = await func(*args, **kwargs)
            self._cache_result(cache_key, result, cache_type)
            return result

        limit = self.limits[api_name]

        # Wait if rate limited
        if not limit.can_make_call():
            wait_time = limit.time_until_available()
            self.stats['rate_limited'] += 1
            logger.warning(
                f"Rate limit reached for {api_name}. "
                f"Waiting {wait_time:.1f}s. "
                f"Queue size: {limit.queue.qsize()}"
            )

            # Add to queue with priority
            priority_score = self.priorities.get(priority, 50)
            await limit.queue.put((priority_score, datetime.now(), func, args, kwargs, cache_key, cache_type))
            self.stats['queued_requests'] += 1

            # Wait until we can proceed
            await asyncio.sleep(wait_time + 0.1)  # Small buffer

        # Execute the call
        limit.record_call()
        self.stats['api_calls'][api_name] = self.stats['api_calls'].get(api_name, 0) + 1

        try:
            result = await func(*args, **kwargs)
            self._cache_result(cache_key, result, cache_type)
            return result
        except Exception as e:
            logger.error(f"API call failed for {api_name}: {e}")
            raise

    def _cache_result(self, cache_key: Optional[str], data: Any, cache_type: str):
        """Cache API result with appropriate TTL"""
        if cache_key:
            ttl = self.cache_ttls.get(cache_type, 3600)  # Default 1 hour
            self.cache[cache_key] = {
                'data': data,
                'expires': datetime.now() + timedelta(seconds=ttl),
                'cached_at': datetime.now().isoformat()
            }
            logger.debug(f"Cached {cache_key} for {ttl}s")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        stats = self.stats.copy()
        stats['rate_limits'] = {}

        for name, limit in self.limits.items():
            stats['rate_limits'][name] = {
                'max_calls': limit.max_calls,
                'time_window': limit.time_window,
                'current_usage': len(limit.calls),
                'available_in': limit.time_until_available(),
                'queue_size': limit.queue.qsize()
            }

        stats['cache_size'] = len(self.cache)
        stats['cache_hit_rate'] = (
            (stats['cached_responses'] / stats['total_requests'] * 100)
            if stats['total_requests'] > 0 else 0
        )

        return stats

    def clear_cache(self, cache_type: Optional[str] = None):
        """Clear cache entries"""
        if cache_type:
            # Clear specific type (would need type tracking)
            self.cache.clear()
            logger.info(f"Cleared cache for {cache_type}")
        else:
            self.cache.clear()
            logger.info("Cleared all cache")

    async def process_queue(self, api_name: str):
        """
        Background task to process queued requests
        Should be run as a separate asyncio task
        """
        if api_name not in self.limits:
            return

        limit = self.limits[api_name]

        while True:
            try:
                # Wait for item in queue
                if limit.queue.empty():
                    await asyncio.sleep(1)
                    continue

                # Wait until rate limit allows
                while not limit.can_make_call():
                    wait_time = limit.time_until_available()
                    await asyncio.sleep(wait_time + 0.1)

                # Get highest priority item
                priority, timestamp, func, args, kwargs, cache_key, cache_type = await limit.queue.get()

                # Execute
                limit.record_call()
                self.stats['api_calls'][api_name] = self.stats['api_calls'].get(api_name, 0) + 1

                try:
                    result = await func(*args, **kwargs)
                    self._cache_result(cache_key, result, cache_type)
                    logger.info(f"Processed queued request for {api_name} (priority: {priority})")
                except Exception as e:
                    logger.error(f"Queued request failed for {api_name}: {e}")

                limit.queue.task_done()

            except Exception as e:
                logger.error(f"Error in queue processor for {api_name}: {e}")
                await asyncio.sleep(1)


# Global instance
rate_limiter = RateLimiterService()


# Convenience decorators
def with_rate_limit(api_name: str, cache_type: str = 'default', priority: str = 'bulk_request'):
    """Decorator to apply rate limiting to async functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            return await rate_limiter.execute_with_limit(
                api_name=api_name,
                func=func,
                cache_key=cache_key,
                cache_type=cache_type,
                priority=priority,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


# Example usage
"""
from services.rate_limiter import rate_limiter, with_rate_limit

# Method 1: Using decorator
@with_rate_limit('alpha_vantage_daily', cache_type='fundamental', priority='fundamental_data')
async def get_fundamental_data(symbol: str):
    # Fetch from Alpha Vantage
    ...

# Method 2: Direct call
async def get_stock_price(symbol: str):
    async def fetch():
        # Fetch logic
        ...

    return await rate_limiter.execute_with_limit(
        api_name='yahoo_finance',
        func=fetch,
        cache_key=f'price:{symbol}',
        cache_type='stock_price',
        priority='real_time_price'
    )

# Start queue processors (in main.py startup)
asyncio.create_task(rate_limiter.process_queue('alpha_vantage_daily'))
asyncio.create_task(rate_limiter.process_queue('tavily_monthly'))
"""
