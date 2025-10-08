"""
Tavily Cache Service
Implements Redis-based caching for Tavily API responses to reduce costs
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import timedelta
import asyncio

logger = logging.getLogger(__name__)


class TavilyCache:
    """
    Redis-based cache for Tavily API responses

    Features:
    - 24-hour TTL for news/sentiment (stale after 1 day)
    - 7-day TTL for macro data (slower moving)
    - Query hashing for cache keys
    - Graceful fallback if Redis unavailable
    - Cost tracking and reporting
    """

    def __init__(self, redis_url: str = None):
        self.redis_client = None
        self.enabled = False

        # Try to initialize Redis
        if redis_url:
            try:
                import redis.asyncio as aioredis
                self.redis_client = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                self.enabled = True
                logger.info("[TavilyCache] Redis cache initialized")
            except ImportError:
                logger.warning("[TavilyCache] redis package not installed, caching disabled")
            except Exception as e:
                logger.warning(f"[TavilyCache] Redis connection failed: {e}, caching disabled")
        else:
            logger.info("[TavilyCache] Redis URL not provided, caching disabled")

        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'cost_saved': 0.0
        }

    def _generate_cache_key(self, query_type: str, symbol: str, params: Dict[str, Any]) -> str:
        """
        Generate deterministic cache key from query parameters

        Args:
            query_type: 'news', 'sentiment', or 'macro'
            symbol: Stock symbol
            params: Search parameters (query, days, domains, etc.)

        Returns:
            SHA256 hash as cache key
        """
        # Sort params for consistent hashing
        param_str = json.dumps(params, sort_keys=True)
        hash_input = f"{query_type}:{symbol}:{param_str}"
        return f"tavily:{hashlib.sha256(hash_input.encode()).hexdigest()}"

    async def get(self, query_type: str, symbol: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached Tavily response

        Returns:
            Cached data if found, None otherwise
        """
        if not self.enabled:
            return None

        try:
            cache_key = self._generate_cache_key(query_type, symbol, params)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                self.stats['hits'] += 1
                # Estimate cost saved (Tavily API ~$0.01 per request)
                self.stats['cost_saved'] += 0.01
                logger.info(f"[TavilyCache] HIT - {query_type} for {symbol}")
                return json.loads(cached_data)
            else:
                self.stats['misses'] += 1
                logger.debug(f"[TavilyCache] MISS - {query_type} for {symbol}")
                return None

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"[TavilyCache] Error retrieving cache: {e}")
            return None

    async def set(
        self,
        query_type: str,
        symbol: str,
        params: Dict[str, Any],
        data: Dict[str, Any],
        ttl_hours: int = None
    ):
        """
        Cache Tavily response

        Args:
            query_type: 'news', 'sentiment', or 'macro'
            symbol: Stock symbol
            params: Search parameters
            data: Tavily response to cache
            ttl_hours: Time-to-live in hours (default: 24 for news/sentiment, 168 for macro)
        """
        if not self.enabled:
            return

        try:
            # Default TTLs based on data type
            if ttl_hours is None:
                if query_type == 'macro':
                    ttl_hours = 168  # 7 days (macro data slower moving)
                else:
                    ttl_hours = 24   # 1 day (news/sentiment expire faster)

            cache_key = self._generate_cache_key(query_type, symbol, params)
            await self.redis_client.set(
                cache_key,
                json.dumps(data),
                ex=timedelta(hours=ttl_hours)
            )

            logger.info(f"[TavilyCache] SET - {query_type} for {symbol} (TTL: {ttl_hours}h)")

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"[TavilyCache] Error setting cache: {e}")

    async def invalidate(self, query_type: str, symbol: str):
        """
        Invalidate all cached entries for a symbol/query_type

        Useful when forcing fresh data (e.g., after major news event)
        """
        if not self.enabled:
            return

        try:
            # Pattern matching to find all keys for this symbol/type
            pattern = f"tavily:*{query_type}*{symbol}*"
            cursor = 0
            deleted = 0

            async for key in self.redis_client.scan_iter(match=pattern):
                await self.redis_client.delete(key)
                deleted += 1

            logger.info(f"[TavilyCache] Invalidated {deleted} entries for {query_type}/{symbol}")

        except Exception as e:
            logger.error(f"[TavilyCache] Error invalidating cache: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {
                'enabled': False,
                'message': 'Redis caching disabled'
            }

        hit_rate = 0.0
        total = self.stats['hits'] + self.stats['misses']
        if total > 0:
            hit_rate = (self.stats['hits'] / total) * 100

        return {
            'enabled': True,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'errors': self.stats['errors'],
            'hit_rate': round(hit_rate, 2),
            'cost_saved': round(self.stats['cost_saved'], 2),
            'total_requests': total
        }

    async def reset_stats(self):
        """Reset statistics (for testing/monitoring)"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'cost_saved': 0.0
        }
        logger.info("[TavilyCache] Statistics reset")

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("[TavilyCache] Redis connection closed")


# Singleton instance
_cache_instance: Optional[TavilyCache] = None


def get_tavily_cache(redis_url: str = None) -> TavilyCache:
    """
    Get or create TavilyCache singleton

    Args:
        redis_url: Redis connection URL (e.g., redis://localhost:6379)

    Returns:
        TavilyCache instance
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = TavilyCache(redis_url)

    return _cache_instance


async def invalidate_symbol_cache(symbol: str):
    """
    Convenience function to invalidate all cached data for a symbol

    Use when major news breaks or you need fresh data
    """
    cache = get_tavily_cache()
    if cache.enabled:
        await asyncio.gather(
            cache.invalidate('news', symbol),
            cache.invalidate('sentiment', symbol),
            cache.invalidate('macro', symbol),
            return_exceptions=True
        )
