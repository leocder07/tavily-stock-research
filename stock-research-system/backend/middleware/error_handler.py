"""Global error handling middleware for the application"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging
import traceback
import time
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware"""

    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process request and handle errors"""

        # Track request timing
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", f"req_{int(time.time()*1000)}")

        try:
            # Add request context
            request.state.request_id = request_id
            request.state.start_time = start_time

            # Process request
            response = await call_next(request)

            # Add timing header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response

        except HTTPException as e:
            # Handle HTTP exceptions
            return await self._handle_http_exception(e, request_id)

        except asyncio.TimeoutError:
            # Handle timeout errors
            return await self._handle_timeout_error(request_id)

        except ValueError as e:
            # Handle validation errors
            return await self._handle_validation_error(e, request_id)

        except ConnectionError as e:
            # Handle connection errors (DB, external services)
            return await self._handle_connection_error(e, request_id)

        except Exception as e:
            # Handle unexpected errors
            return await self._handle_unexpected_error(e, request_id)

    async def _handle_http_exception(self, exc: HTTPException, request_id: str) -> JSONResponse:
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP Exception in request {request_id}: {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"X-Request-ID": request_id}
        )

    async def _handle_timeout_error(self, request_id: str) -> JSONResponse:
        """Handle timeout errors"""
        logger.error(f"Timeout error in request {request_id}")

        return JSONResponse(
            status_code=504,
            content={
                "error": "timeout_error",
                "message": "Request processing timed out",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"X-Request-ID": request_id}
        )

    async def _handle_validation_error(self, exc: ValueError, request_id: str) -> JSONResponse:
        """Handle validation errors"""
        logger.warning(f"Validation error in request {request_id}: {str(exc)}")

        return JSONResponse(
            status_code=400,
            content={
                "error": "validation_error",
                "message": str(exc),
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"X-Request-ID": request_id}
        )

    async def _handle_connection_error(self, exc: ConnectionError, request_id: str) -> JSONResponse:
        """Handle connection errors"""
        logger.error(f"Connection error in request {request_id}: {str(exc)}")

        return JSONResponse(
            status_code=503,
            content={
                "error": "connection_error",
                "message": "Service temporarily unavailable",
                "details": str(exc) if self.debug else None,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"X-Request-ID": request_id}
        )

    async def _handle_unexpected_error(self, exc: Exception, request_id: str) -> JSONResponse:
        """Handle unexpected errors"""
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error in request {request_id}: {error_trace}")

        # Log full error details
        logger.error(f"Error type: {type(exc).__name__}")
        logger.error(f"Error message: {str(exc)}")

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "details": error_trace if self.debug else None,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"X-Request-ID": request_id}
        )


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Circuit breaker pattern for external service calls"""

    def __init__(self, app, failure_threshold: int = 5, timeout_duration: int = 60):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.failures = {}
        self.circuit_open_until = {}

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Check circuit breaker before processing request"""

        # Check if circuit is open for this endpoint
        endpoint = str(request.url.path)

        if endpoint in self.circuit_open_until:
            if time.time() < self.circuit_open_until[endpoint]:
                logger.warning(f"Circuit breaker open for {endpoint}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "circuit_breaker_open",
                        "message": "Service temporarily disabled due to repeated failures",
                        "retry_after": int(self.circuit_open_until[endpoint] - time.time())
                    }
                )
            else:
                # Reset circuit
                del self.circuit_open_until[endpoint]
                self.failures[endpoint] = 0

        try:
            response = await call_next(request)

            # Reset failure count on success
            if response.status_code < 500:
                self.failures[endpoint] = 0

            return response

        except Exception as e:
            # Increment failure count
            self.failures[endpoint] = self.failures.get(endpoint, 0) + 1

            # Open circuit if threshold reached
            if self.failures[endpoint] >= self.failure_threshold:
                self.circuit_open_until[endpoint] = time.time() + self.timeout_duration
                logger.error(f"Circuit breaker opened for {endpoint}")

            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_times = {}

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Enforce rate limits"""

        # Get client identifier (IP address or user ID)
        client_id = request.client.host if request.client else "unknown"

        # Clean old requests
        current_time = time.time()
        if client_id in self.request_times:
            self.request_times[client_id] = [
                t for t in self.request_times[client_id]
                if current_time - t < 60
            ]

        # Check rate limit
        if client_id in self.request_times:
            if len(self.request_times[client_id]) >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for {client_id}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Maximum {self.requests_per_minute} requests per minute exceeded",
                        "retry_after": 60
                    }
                )

        # Record request
        if client_id not in self.request_times:
            self.request_times[client_id] = []
        self.request_times[client_id].append(current_time)

        # Process request
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/Response logging middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Log requests and responses"""

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        logger.debug(f"Headers: {dict(request.headers)}")

        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )

        return response


def setup_error_handling(app, debug: bool = False):
    """Setup all error handling middleware"""

    # Add middleware in order of execution
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    app.add_middleware(CircuitBreakerMiddleware, failure_threshold=5, timeout_duration=60)
    app.add_middleware(ErrorHandlingMiddleware, debug=debug)

    # Add exception handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found",
                "message": "Requested resource not found",
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=405,
            content={
                "error": "method_not_allowed",
                "message": f"Method {request.method} not allowed for this endpoint",
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: Exception):
        logger.error(f"Internal server error: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An internal error occurred",
                "request_id": getattr(request.state, 'request_id', 'unknown')
            }
        )

    logger.info("Error handling middleware configured")