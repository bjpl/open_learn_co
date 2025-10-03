"""
Logging Middleware for Request/Response Tracking

This middleware provides:
- Automatic request/response logging
- Performance timing
- Error tracking
- Correlation ID injection
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import get_logger, set_trace_context, clear_trace_context


logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""

    def __init__(self, app: ASGIApp, exclude_paths: list[str] | None = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Generate or extract trace ID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        # Set trace context
        set_trace_context(
            trace_id=trace_id,
            request_id=request_id,
            user_id=request.headers.get("X-User-ID")
        )

        # Log request
        start_time = time.time()

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Process request
        response = None
        error = None

        try:
            response = await call_next(request)
            return response

        except Exception as e:
            error = e
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            if response:
                logger.info(
                    "request_completed",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2),
                )

                # Add trace headers to response
                response.headers["X-Trace-ID"] = trace_id
                response.headers["X-Request-ID"] = request_id

            # Clear trace context
            clear_trace_context()


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed performance logging"""

    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold_ms: float = 1000.0,
        log_all_requests: bool = False
    ):
        super().__init__(app)
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.log_all_requests = log_all_requests

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # Log slow requests
        if duration_ms > self.slow_request_threshold_ms:
            logger.warning(
                "slow_request",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                threshold_ms=self.slow_request_threshold_ms,
            )

        # Optionally log all requests with timing
        elif self.log_all_requests:
            logger.debug(
                "request_timing",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
            )

        return response


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured error logging"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)

        except Exception as e:
            # Log detailed error information
            logger.exception(
                "unhandled_exception",
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__,
                error_message=str(e),
                query_params=str(request.query_params),
            )

            # Re-raise to be handled by exception handlers
            raise
