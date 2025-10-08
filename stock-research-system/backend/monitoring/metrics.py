"""Monitoring and metrics collection for Stock Research System"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import os

logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter(
    'stock_research_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'stock_research_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'stock_research_active_requests',
    'Number of active requests'
)

agent_execution_time = Histogram(
    'stock_research_agent_execution_seconds',
    'Agent execution time in seconds',
    ['agent_type']
)

cache_hits = Counter(
    'stock_research_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'stock_research_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

workflow_executions = Counter(
    'stock_research_workflow_executions_total',
    'Total number of workflow executions',
    ['status']
)

workflow_duration = Histogram(
    'stock_research_workflow_duration_seconds',
    'Workflow execution duration in seconds'
)

api_errors = Counter(
    'stock_research_api_errors_total',
    'Total number of API errors',
    ['error_type', 'endpoint']
)

tavily_api_calls = Counter(
    'stock_research_tavily_api_calls_total',
    'Total number of Tavily API calls',
    ['method']
)

openai_api_calls = Counter(
    'stock_research_openai_api_calls_total',
    'Total number of OpenAI API calls',
    ['model']
)

mongodb_operations = Counter(
    'stock_research_mongodb_operations_total',
    'Total number of MongoDB operations',
    ['operation']
)

redis_operations = Counter(
    'stock_research_redis_operations_total',
    'Total number of Redis operations',
    ['operation']
)


class MetricsCollector:
    """Centralized metrics collection and monitoring"""

    def __init__(self, sentry_dsn: Optional[str] = None):
        """Initialize metrics collector

        Args:
            sentry_dsn: Sentry DSN for error tracking
        """
        self.sentry_dsn = sentry_dsn or os.getenv('SENTRY_DSN')

        # Initialize Sentry if DSN provided
        if self.sentry_dsn:
            self._init_sentry()

    def _init_sentry(self):
        """Initialize Sentry error tracking"""
        try:
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    LoggingIntegration(
                        level=logging.INFO,
                        event_level=logging.ERROR
                    )
                ],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment=os.getenv('ENVIRONMENT', 'development'),
                release=os.getenv('APP_VERSION', 'unknown')
            )
            logger.info("Sentry initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    @contextmanager
    def track_request(self, method: str, endpoint: str):
        """Context manager to track request metrics

        Args:
            method: HTTP method
            endpoint: API endpoint
        """
        active_requests.inc()
        start_time = time.time()

        try:
            yield
            status = 'success'
        except Exception as e:
            status = 'error'
            api_errors.labels(
                error_type=type(e).__name__,
                endpoint=endpoint
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            active_requests.dec()

    def track_agent_execution(self, agent_type: str):
        """Decorator to track agent execution time

        Args:
            agent_type: Type of agent being tracked
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    agent_execution_time.labels(
                        agent_type=agent_type
                    ).observe(duration)
                    logger.info(f"Agent {agent_type} executed in {duration:.2f}s")
            return wrapper
        return decorator

    def track_workflow_execution(self):
        """Decorator to track workflow execution"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    workflow_executions.labels(status='success').inc()
                    return result
                except Exception as e:
                    workflow_executions.labels(status='error').inc()
                    logger.error(f"Workflow execution failed: {e}")
                    raise
                finally:
                    duration = time.time() - start_time
                    workflow_duration.observe(duration)
                    logger.info(f"Workflow executed in {duration:.2f}s")
            return wrapper
        return decorator

    def record_cache_hit(self, cache_type: str):
        """Record a cache hit

        Args:
            cache_type: Type of cache (e.g., 'redis', 'memory')
        """
        cache_hits.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """Record a cache miss

        Args:
            cache_type: Type of cache
        """
        cache_misses.labels(cache_type=cache_type).inc()

    def record_tavily_call(self, method: str):
        """Record a Tavily API call

        Args:
            method: Tavily API method (e.g., 'search', 'extract')
        """
        tavily_api_calls.labels(method=method).inc()

    def record_openai_call(self, model: str):
        """Record an OpenAI API call

        Args:
            model: OpenAI model used
        """
        openai_api_calls.labels(model=model).inc()

    def record_mongodb_operation(self, operation: str):
        """Record a MongoDB operation

        Args:
            operation: MongoDB operation (e.g., 'find', 'insert')
        """
        mongodb_operations.labels(operation=operation).inc()

    def record_redis_operation(self, operation: str):
        """Record a Redis operation

        Args:
            operation: Redis operation (e.g., 'get', 'set')
        """
        redis_operations.labels(operation=operation).inc()

    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format

        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest()


# Singleton instance
_metrics_instance = None

def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector instance

    Returns:
        MetricsCollector instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance


# Custom logging formatter with trace ID
class TraceIDFormatter(logging.Formatter):
    """Custom formatter that includes trace ID"""

    def format(self, record):
        # Add trace ID if available
        if hasattr(record, 'trace_id'):
            record.msg = f"[{record.trace_id}] {record.msg}"
        return super().format(record)


def setup_logging():
    """Setup structured logging with trace ID"""
    formatter = TraceIDFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler]
    )

    # Set specific log levels
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    logging.getLogger('agents').setLevel(logging.INFO)
    logging.getLogger('cache').setLevel(logging.DEBUG)