"""
Advanced Retry Manager with Multiple Strategies
Implements exponential backoff, jitter, circuit breaking, and adaptive retry
"""

import asyncio
import logging
import random
import time
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import math
from datetime import datetime, timedelta
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Available retry strategies"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    ADAPTIVE = "adaptive"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    jitter_range: float = 0.3
    backoff_factor: float = 2.0
    retry_on_exceptions: tuple = (Exception,)
    retry_on_status_codes: List[int] = None
    circuit_breaker_threshold: int = 10
    circuit_breaker_timeout: int = 60


class RetryMetrics:
    """Track retry metrics for monitoring and adaptive behavior"""

    def __init__(self, window_size: int = 100):
        self.attempts = deque(maxlen=window_size)
        self.successes = deque(maxlen=window_size)
        self.failures = deque(maxlen=window_size)
        self.latencies = deque(maxlen=window_size)
        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0

    def record_attempt(self):
        """Record a retry attempt"""
        self.attempts.append(time.time())
        self.total_attempts += 1

    def record_success(self, latency: float):
        """Record a successful attempt"""
        self.successes.append(time.time())
        self.latencies.append(latency)
        self.total_successes += 1

    def record_failure(self):
        """Record a failed attempt"""
        self.failures.append(time.time())
        self.total_failures += 1

    def get_success_rate(self) -> float:
        """Calculate recent success rate"""
        if not self.attempts:
            return 0.0
        recent_window = time.time() - 300  # Last 5 minutes
        recent_successes = sum(1 for t in self.successes if t > recent_window)
        recent_attempts = sum(1 for t in self.attempts if t > recent_window)
        return recent_successes / recent_attempts if recent_attempts > 0 else 0.0

    def get_average_latency(self) -> float:
        """Calculate average latency"""
        return np.mean(self.latencies) if self.latencies else 0.0

    def get_p95_latency(self) -> float:
        """Calculate 95th percentile latency"""
        return np.percentile(self.latencies, 95) if self.latencies else 0.0


class RetryStrategyBase(ABC):
    """Base class for retry strategies"""

    @abstractmethod
    def calculate_delay(self, attempt: int, config: RetryConfig, metrics: RetryMetrics) -> float:
        """Calculate delay for the next retry attempt"""
        pass


class ExponentialBackoffStrategy(RetryStrategyBase):
    """Exponential backoff with jitter"""

    def calculate_delay(self, attempt: int, config: RetryConfig, metrics: RetryMetrics) -> float:
        delay = min(
            config.base_delay * (config.backoff_factor ** attempt),
            config.max_delay
        )

        if config.jitter:
            jitter = delay * random.uniform(-config.jitter_range, config.jitter_range)
            delay = max(0.1, delay + jitter)

        return delay


class LinearBackoffStrategy(RetryStrategyBase):
    """Linear backoff strategy"""

    def calculate_delay(self, attempt: int, config: RetryConfig, metrics: RetryMetrics) -> float:
        delay = min(
            config.base_delay * (attempt + 1),
            config.max_delay
        )

        if config.jitter:
            jitter = delay * random.uniform(-config.jitter_range, config.jitter_range)
            delay = max(0.1, delay + jitter)

        return delay


class FibonacciBackoffStrategy(RetryStrategyBase):
    """Fibonacci sequence based backoff"""

    def __init__(self):
        self.fib_cache = [1, 1]

    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number"""
        while len(self.fib_cache) <= n:
            self.fib_cache.append(self.fib_cache[-1] + self.fib_cache[-2])
        return self.fib_cache[n]

    def calculate_delay(self, attempt: int, config: RetryConfig, metrics: RetryMetrics) -> float:
        fib_value = self._fibonacci(attempt)
        delay = min(config.base_delay * fib_value, config.max_delay)

        if config.jitter:
            jitter = delay * random.uniform(-config.jitter_range, config.jitter_range)
            delay = max(0.1, delay + jitter)

        return delay


class AdaptiveBackoffStrategy(RetryStrategyBase):
    """
    Adaptive backoff that adjusts based on system performance
    Uses machine learning-inspired approach to optimize retry delays
    """

    def __init__(self):
        self.delay_history = deque(maxlen=50)
        self.success_delays = deque(maxlen=50)

    def calculate_delay(self, attempt: int, config: RetryConfig, metrics: RetryMetrics) -> float:
        # Base exponential calculation
        base_delay = min(
            config.base_delay * (config.backoff_factor ** attempt),
            config.max_delay
        )

        # Adaptive adjustments based on metrics
        success_rate = metrics.get_success_rate()
        avg_latency = metrics.get_average_latency()
        p95_latency = metrics.get_p95_latency()

        # Adjust delay based on success rate
        if success_rate > 0.8:
            # High success rate, reduce delay
            adjustment_factor = 0.7
        elif success_rate < 0.3:
            # Low success rate, increase delay
            adjustment_factor = 1.5
        else:
            # Normal range
            adjustment_factor = 1.0

        # Further adjust based on latency trends
        if p95_latency > avg_latency * 2:
            # High variance in latency, increase delay
            adjustment_factor *= 1.2

        adjusted_delay = base_delay * adjustment_factor

        # Apply jitter
        if config.jitter:
            jitter = adjusted_delay * random.uniform(-config.jitter_range, config.jitter_range)
            adjusted_delay = max(0.1, adjusted_delay + jitter)

        # Cap at max delay
        final_delay = min(adjusted_delay, config.max_delay)

        # Learn from successful attempts
        if metrics.total_successes > 0 and self.success_delays:
            # Use weighted average of successful delays
            optimal_delay = np.mean(self.success_delays)
            final_delay = 0.7 * final_delay + 0.3 * optimal_delay

        self.delay_history.append(final_delay)

        return final_delay

    def record_success(self, delay: float):
        """Record a successful retry delay for learning"""
        self.success_delays.append(delay)


class RetryManager:
    """
    Main retry manager with multiple strategies and circuit breaking
    """

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.metrics = RetryMetrics()
        self.circuit_breaker_failures = 0
        self.circuit_breaker_reset_time = None

        # Initialize strategies
        self.strategies = {
            RetryStrategy.EXPONENTIAL: ExponentialBackoffStrategy(),
            RetryStrategy.LINEAR: LinearBackoffStrategy(),
            RetryStrategy.FIBONACCI: FibonacciBackoffStrategy(),
            RetryStrategy.ADAPTIVE: AdaptiveBackoffStrategy(),
        }

        self.current_strategy = self.strategies[self.config.strategy]

    async def execute_with_retry(self,
                                func: Callable,
                                *args,
                                on_retry: Optional[Callable] = None,
                                **kwargs) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Async function to execute
            on_retry: Optional callback for each retry attempt
            *args, **kwargs: Arguments for func

        Returns:
            Result from func

        Raises:
            Last exception if all retries fail
        """
        # Check circuit breaker
        if self._is_circuit_open():
            raise Exception("Circuit breaker is open. Service unavailable.")

        last_exception = None
        start_time = time.time()

        for attempt in range(self.config.max_retries):
            try:
                self.metrics.record_attempt()

                # Execute function
                result = await func(*args, **kwargs)

                # Record success
                latency = time.time() - start_time
                self.metrics.record_success(latency)

                # Reset circuit breaker on success
                self._reset_circuit_breaker()

                # Update adaptive strategy if applicable
                if isinstance(self.current_strategy, AdaptiveBackoffStrategy):
                    delay = self.current_strategy.calculate_delay(
                        attempt, self.config, self.metrics
                    )
                    self.current_strategy.record_success(delay)

                return result

            except self.config.retry_on_exceptions as e:
                last_exception = e
                self.metrics.record_failure()

                # Check if we should retry
                if attempt >= self.config.max_retries - 1:
                    self._record_circuit_breaker_failure()
                    logger.error(f"All {self.config.max_retries} retry attempts failed")
                    raise e

                # Calculate delay
                delay = self.current_strategy.calculate_delay(
                    attempt, self.config, self.metrics
                )

                # Log retry attempt
                logger.warning(
                    f"Retry attempt {attempt + 1}/{self.config.max_retries} "
                    f"failed with {type(e).__name__}. "
                    f"Retrying in {delay:.2f}s..."
                )

                # Call retry callback if provided
                if on_retry:
                    await on_retry(attempt, delay, e)

                # Wait before retry
                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        raise last_exception

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.circuit_breaker_failures >= self.config.circuit_breaker_threshold:
            if self.circuit_breaker_reset_time is None:
                self.circuit_breaker_reset_time = (
                    datetime.utcnow() +
                    timedelta(seconds=self.config.circuit_breaker_timeout)
                )
                logger.error(
                    f"Circuit breaker opened after {self.circuit_breaker_failures} failures"
                )

            if datetime.utcnow() < self.circuit_breaker_reset_time:
                return True
            else:
                # Reset circuit breaker after timeout
                self._reset_circuit_breaker()
                logger.info("Circuit breaker reset after timeout")

        return False

    def _reset_circuit_breaker(self):
        """Reset circuit breaker"""
        self.circuit_breaker_failures = 0
        self.circuit_breaker_reset_time = None

    def _record_circuit_breaker_failure(self):
        """Record a failure for circuit breaker"""
        self.circuit_breaker_failures += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get retry metrics for monitoring"""
        return {
            'total_attempts': self.metrics.total_attempts,
            'total_successes': self.metrics.total_successes,
            'total_failures': self.metrics.total_failures,
            'success_rate': self.metrics.get_success_rate(),
            'average_latency': self.metrics.get_average_latency(),
            'p95_latency': self.metrics.get_p95_latency(),
            'circuit_breaker_open': self._is_circuit_open(),
            'circuit_breaker_failures': self.circuit_breaker_failures,
            'strategy': self.config.strategy.value
        }

    def switch_strategy(self, strategy: RetryStrategy):
        """Dynamically switch retry strategy"""
        if strategy in self.strategies:
            self.current_strategy = self.strategies[strategy]
            self.config.strategy = strategy
            logger.info(f"Switched to {strategy.value} retry strategy")
        else:
            logger.warning(f"Unknown strategy: {strategy}")


class SmartRetryOrchestrator:
    """
    Orchestrates multiple retry managers for different services
    with intelligent strategy selection
    """

    def __init__(self):
        self.retry_managers = {}
        self.performance_history = {}

    def get_or_create_manager(self, service: str, config: RetryConfig = None) -> RetryManager:
        """Get or create a retry manager for a service"""
        if service not in self.retry_managers:
            # Select optimal strategy based on history
            if service in self.performance_history:
                config = config or RetryConfig()
                config.strategy = self._select_optimal_strategy(service)

            self.retry_managers[service] = RetryManager(config or RetryConfig())

        return self.retry_managers[service]

    def _select_optimal_strategy(self, service: str) -> RetryStrategy:
        """Select optimal retry strategy based on performance history"""
        history = self.performance_history.get(service, {})

        # Simple heuristic for strategy selection
        if history.get('variance_high', False):
            return RetryStrategy.ADAPTIVE
        elif history.get('failure_rate', 0) > 0.5:
            return RetryStrategy.EXPONENTIAL
        else:
            return RetryStrategy.LINEAR

    async def execute_with_smart_retry(self,
                                      service: str,
                                      func: Callable,
                                      *args,
                                      **kwargs) -> Any:
        """Execute with intelligent retry management"""
        manager = self.get_or_create_manager(service)

        try:
            result = await manager.execute_with_retry(func, *args, **kwargs)

            # Update performance history
            self._update_performance_history(service, manager.get_metrics())

            return result

        except Exception as e:
            # Record failure in performance history
            self._update_performance_history(service, manager.get_metrics())
            raise e

    def _update_performance_history(self, service: str, metrics: Dict[str, Any]):
        """Update performance history for a service"""
        if service not in self.performance_history:
            self.performance_history[service] = {}

        history = self.performance_history[service]
        history['last_metrics'] = metrics
        history['failure_rate'] = 1 - metrics.get('success_rate', 0)

        # Check for high variance
        if metrics.get('p95_latency', 0) > metrics.get('average_latency', 0) * 2:
            history['variance_high'] = True

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all services"""
        return {
            service: manager.get_metrics()
            for service, manager in self.retry_managers.items()
        }