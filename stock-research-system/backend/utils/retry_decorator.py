"""Retry decorators with exponential backoff for external API calls"""

import asyncio
import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Type, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)


def exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        max_delay: Maximum delay between retries
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    # Log attempt
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt}/{max_retries} for {func.__name__}")

                    # Execute function
                    result = await func(*args, **kwargs)

                    # Success - log and return
                    if attempt > 0:
                        logger.info(f"Successfully completed {func.__name__} after {attempt} retries")

                    return result

                except exceptions as e:
                    last_exception = e

                    # Check if we should retry
                    if attempt >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise

                    # Calculate delay
                    delay = min(initial_delay * (exponential_base ** attempt), max_delay)

                    # Add jitter if enabled
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Error in {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds... "
                        f"(Attempt {attempt + 1}/{max_retries + 1})"
                    )

                    # Wait before retry
                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    # Log attempt
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt}/{max_retries} for {func.__name__}")

                    # Execute function
                    result = func(*args, **kwargs)

                    # Success - log and return
                    if attempt > 0:
                        logger.info(f"Successfully completed {func.__name__} after {attempt} retries")

                    return result

                except exceptions as e:
                    last_exception = e

                    # Check if we should retry
                    if attempt >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise

                    # Calculate delay
                    delay = min(initial_delay * (exponential_base ** attempt), max_delay)

                    # Add jitter if enabled
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Error in {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds... "
                        f"(Attempt {attempt + 1}/{max_retries + 1})"
                    )

                    # Wait before retry
                    time.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_on_network_error(
    max_retries: int = 3,
    initial_delay: float = 1.0
):
    """
    Specialized retry decorator for network-related errors.

    Retries on:
    - ConnectionError
    - TimeoutError
    - OSError (network-related)
    """
    network_exceptions = (
        ConnectionError,
        TimeoutError,
        OSError,
        asyncio.TimeoutError,
    )

    return exponential_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        exceptions=network_exceptions,
        jitter=True
    )


def retry_on_api_error(
    max_retries: int = 5,
    initial_delay: float = 2.0
):
    """
    Specialized retry decorator for API-related errors.

    Includes longer delays and more retries for rate limiting.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(f"API call {func.__name__} succeeded after {attempt} retries")

                    return result

                except Exception as e:
                    last_exception = e

                    # Check for rate limiting (status code 429)
                    if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        if e.response.status_code == 429:
                            # Rate limited - use longer delay
                            retry_after = e.response.headers.get('Retry-After', 60)
                            delay = float(retry_after)
                            logger.warning(f"Rate limited on {func.__name__}. Waiting {delay} seconds...")
                            await asyncio.sleep(delay)
                            continue

                    # Regular retry logic
                    if attempt >= max_retries:
                        logger.error(f"Max API retries exceeded for {func.__name__}: {str(e)}")
                        raise

                    # Exponential backoff with jitter
                    delay = min(initial_delay * (2 ** attempt), 60.0)
                    delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"API error in {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )

                    await asyncio.sleep(delay)

            if last_exception:
                raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(f"API call {func.__name__} succeeded after {attempt} retries")

                    return result

                except Exception as e:
                    last_exception = e

                    # Check for rate limiting
                    if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        if e.response.status_code == 429:
                            retry_after = e.response.headers.get('Retry-After', 60)
                            delay = float(retry_after)
                            logger.warning(f"Rate limited on {func.__name__}. Waiting {delay} seconds...")
                            time.sleep(delay)
                            continue

                    if attempt >= max_retries:
                        logger.error(f"Max API retries exceeded for {func.__name__}: {str(e)}")
                        raise

                    delay = min(initial_delay * (2 ** attempt), 60.0)
                    delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"API error in {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )

                    time.sleep(delay)

            if last_exception:
                raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_on_database_error(
    max_retries: int = 3,
    initial_delay: float = 0.5
):
    """
    Specialized retry decorator for database operations.

    Handles:
    - Connection pool exhaustion
    - Temporary connection failures
    - Lock timeouts
    """

    # Common database exceptions
    db_exceptions = (
        ConnectionError,
        TimeoutError,
        # Add specific database exceptions as needed
    )

    return exponential_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        exponential_base=2.0,
        max_delay=10.0,
        exceptions=db_exceptions,
        jitter=True
    )


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: Type[Exception] = Exception
):
    """
    Circuit breaker pattern decorator.

    Opens circuit after failure_threshold consecutive failures.
    Attempts recovery after recovery_timeout seconds.
    """

    def decorator(func: Callable) -> Callable:
        # Circuit breaker state
        func._failures = 0
        func._last_failure_time = None
        func._circuit_open = False

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Check if circuit is open
            if func._circuit_open:
                if func._last_failure_time:
                    time_since_failure = time.time() - func._last_failure_time
                    if time_since_failure < recovery_timeout:
                        raise Exception(
                            f"Circuit breaker is open for {func.__name__}. "
                            f"Retry after {recovery_timeout - time_since_failure:.0f} seconds."
                        )
                    else:
                        # Attempt recovery
                        func._circuit_open = False
                        func._failures = 0
                        logger.info(f"Circuit breaker attempting recovery for {func.__name__}")

            try:
                result = await func(*args, **kwargs)

                # Success - reset failure count
                func._failures = 0
                if func._circuit_open:
                    func._circuit_open = False
                    logger.info(f"Circuit breaker recovered for {func.__name__}")

                return result

            except expected_exception as e:
                func._failures += 1
                func._last_failure_time = time.time()

                if func._failures >= failure_threshold:
                    func._circuit_open = True
                    logger.error(
                        f"Circuit breaker opened for {func.__name__} "
                        f"after {func._failures} failures"
                    )

                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Check if circuit is open
            if func._circuit_open:
                if func._last_failure_time:
                    time_since_failure = time.time() - func._last_failure_time
                    if time_since_failure < recovery_timeout:
                        raise Exception(
                            f"Circuit breaker is open for {func.__name__}. "
                            f"Retry after {recovery_timeout - time_since_failure:.0f} seconds."
                        )
                    else:
                        func._circuit_open = False
                        func._failures = 0
                        logger.info(f"Circuit breaker attempting recovery for {func.__name__}")

            try:
                result = func(*args, **kwargs)

                func._failures = 0
                if func._circuit_open:
                    func._circuit_open = False
                    logger.info(f"Circuit breaker recovered for {func.__name__}")

                return result

            except expected_exception as e:
                func._failures += 1
                func._last_failure_time = time.time()

                if func._failures >= failure_threshold:
                    func._circuit_open = True
                    logger.error(
                        f"Circuit breaker opened for {func.__name__} "
                        f"after {func._failures} failures"
                    )

                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Convenience function for combining multiple retry strategies
def robust_external_call(
    max_retries: int = 5,
    circuit_breaker_threshold: int = 10
):
    """
    Combines retry and circuit breaker patterns for robust external calls.
    """

    def decorator(func: Callable) -> Callable:
        # Apply decorators in order
        func = retry_on_api_error(max_retries=max_retries)(func)
        func = circuit_breaker(failure_threshold=circuit_breaker_threshold)(func)
        return func

    return decorator