"""
Async Data Service with Circuit Breaker, Connection Pooling, and Retry Logic
Production-ready service for fetching real-time financial data
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
from dataclasses import dataclass
import hashlib
import json
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: type = Exception


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker is OPEN. Service unavailable.")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try again"""
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.config.recovery_timeout)

    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")


class RequestDeduplicator:
    """Prevents redundant API calls for identical requests"""

    def __init__(self, ttl: int = 60):
        self.cache = {}
        self.ttl = ttl
        self.locks = defaultdict(asyncio.Lock)

    def _get_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique key for request"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def deduplicate(self, func: Callable, func_name: str, *args, **kwargs):
        """Execute function only if not already in progress or cached"""
        key = self._get_key(func_name, args, kwargs)

        # Check cache first
        if key in self.cache:
            cached_result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.debug(f"Returning cached result for {func_name}")
                return cached_result

        # Use lock to prevent concurrent identical requests
        async with self.locks[key]:
            # Double-check cache after acquiring lock
            if key in self.cache:
                cached_result, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            self.cache[key] = (result, time.time())

            # Clean old cache entries
            self._cleanup_cache()

            return result

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]


class AsyncDataService:
    """
    Production-ready async data service with:
    - Connection pooling
    - Circuit breaker pattern
    - Request deduplication
    - Retry with exponential backoff
    """

    def __init__(self,
                 max_connections: int = 100,
                 timeout: aiohttp.ClientTimeout = None):

        # Connection pooling configuration
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=30,
            ttl_dns_cache=300
        )

        # Default timeout configuration for production
        if timeout is None:
            timeout = aiohttp.ClientTimeout(
                total=60,      # Total timeout for the entire request
                connect=10,    # Timeout for establishing connection
                sock_read=30   # Timeout for reading response
            )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

        # Circuit breakers for different services
        self.circuit_breakers = {
            'tavily': CircuitBreaker(CircuitBreakerConfig()),
            'openai': CircuitBreaker(CircuitBreakerConfig()),
            'market_data': CircuitBreaker(CircuitBreakerConfig()),
        }

        # Request deduplication
        self.deduplicator = RequestDeduplicator(ttl=60)

        # Metrics tracking
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0,
            'circuit_breaks': 0,
        }

    async def fetch_with_retry(self,
                              service_name: str,
                              fetch_func: Callable,
                              *args,
                              max_retries: int = 5,
                              **kwargs) -> Optional[Any]:
        """
        Fetch data with exponential backoff retry strategy

        Args:
            service_name: Name of the service for circuit breaker
            fetch_func: Async function to execute
            max_retries: Maximum number of retry attempts

        Returns:
            Result from fetch_func or None if all retries failed
        """
        self.metrics['total_requests'] += 1

        # Get circuit breaker for service
        circuit_breaker = self.circuit_breakers.get(
            service_name,
            self.circuit_breakers['market_data']
        )

        # Exponential backoff configuration
        base_delay = 1  # Start with 1 second
        max_delay = 32  # Cap at 32 seconds
        jitter_range = 0.3  # Add ±30% jitter

        for attempt in range(max_retries):
            try:
                # Use circuit breaker
                result = await circuit_breaker.call(
                    self.deduplicator.deduplicate,
                    fetch_func,
                    f"{service_name}_{fetch_func.__name__}",
                    *args,
                    **kwargs
                )

                self.metrics['successful_requests'] += 1
                return result

            except Exception as e:
                self.metrics['failed_requests'] += 1

                if attempt < max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    import random
                    jitter = delay * random.uniform(-jitter_range, jitter_range)
                    actual_delay = max(0.1, delay + jitter)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {service_name}. "
                        f"Retrying in {actual_delay:.2f}s. Error: {str(e)}"
                    )

                    self.metrics['retry_attempts'] += 1
                    await asyncio.sleep(actual_delay)
                else:
                    logger.error(
                        f"All {max_retries} attempts failed for {service_name}. Error: {str(e)}"
                    )
                    raise

        return None

    async def fetch_market_data(self,
                               symbol: str,
                               data_providers: List[str] = None) -> Dict[str, Any]:
        """
        Fetch market data with fallback to multiple providers

        Args:
            symbol: Stock symbol
            data_providers: List of data providers to try in order

        Returns:
            Market data dictionary
        """
        if data_providers is None:
            data_providers = ['tavily', 'yfinance', 'alphavantage']

        for provider in data_providers:
            try:
                if provider == 'tavily':
                    return await self.fetch_with_retry(
                        'tavily',
                        self._fetch_tavily_data,
                        symbol
                    )
                elif provider == 'yfinance':
                    return await self.fetch_with_retry(
                        'yfinance',
                        self._fetch_yfinance_data,
                        symbol
                    )
                elif provider == 'alphavantage':
                    return await self.fetch_with_retry(
                        'alphavantage',
                        self._fetch_alphavantage_data,
                        symbol
                    )
            except Exception as e:
                logger.warning(f"Provider {provider} failed for {symbol}: {str(e)}")
                continue

        # Return partial data if all providers fail
        return {
            'symbol': symbol,
            'status': 'partial',
            'error': 'All data providers unavailable',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _fetch_tavily_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Tavily API"""
        # Implementation will use actual Tavily client
        # This is a placeholder for the actual implementation
        return {
            'symbol': symbol,
            'source': 'tavily',
            'data': {},
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _fetch_yfinance_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Yahoo Finance"""
        # Implementation for Yahoo Finance backup
        return {
            'symbol': symbol,
            'source': 'yfinance',
            'data': {},
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _fetch_alphavantage_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from Alpha Vantage"""
        # Implementation for Alpha Vantage backup
        return {
            'symbol': symbol,
            'source': 'alphavantage',
            'data': {},
            'timestamp': datetime.utcnow().isoformat()
        }

    async def batch_fetch(self,
                         symbols: List[str],
                         fetch_func: Callable,
                         batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Batch fetch data for multiple symbols

        Args:
            symbols: List of stock symbols
            fetch_func: Function to fetch data for each symbol
            batch_size: Number of concurrent requests

        Returns:
            List of results for each symbol
        """
        results = []

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_tasks = [fetch_func(symbol) for symbol in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for symbol, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to fetch data for {symbol}: {str(result)}")
                    results.append({
                        'symbol': symbol,
                        'error': str(result),
                        'status': 'failed'
                    })
                else:
                    results.append(result)

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics for monitoring"""
        return {
            **self.metrics,
            'circuit_breaker_states': {
                name: breaker.state.value
                for name, breaker in self.circuit_breakers.items()
            },
            'cache_size': len(self.deduplicator.cache),
            'timestamp': datetime.utcnow().isoformat()
        }

    async def close(self):
        """Clean up resources"""
        await self.session.close()