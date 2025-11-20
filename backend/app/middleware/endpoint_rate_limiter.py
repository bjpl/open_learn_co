"""
Simple endpoint-specific rate limiting decorator
For endpoints that need custom rate limits beyond middleware
"""

import time
from functools import wraps
from typing import Dict, Callable, Any
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import HTTPException, status, Request
from starlette.responses import JSONResponse


class SimpleRateLimiter:
    """
    In-memory rate limiter for specific endpoints

    Uses a simple sliding window algorithm with in-memory storage.
    For production with multiple workers, consider using Redis-based rate limiting.
    """

    def __init__(self):
        # Storage: {identifier: [(timestamp, count)]}
        self._requests: Dict[str, list] = defaultdict(list)

    def _clean_old_requests(self, identifier: str, window_seconds: int) -> None:
        """Remove requests older than the window"""
        if identifier not in self._requests:
            return

        cutoff_time = time.time() - window_seconds
        self._requests[identifier] = [
            (ts, count) for ts, count in self._requests[identifier]
            if ts > cutoff_time
        ]

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request should be allowed

        Args:
            identifier: Unique identifier (email, IP, user_id)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        self._clean_old_requests(identifier, window_seconds)

        current_time = time.time()
        request_count = len(self._requests[identifier])

        if request_count >= max_requests:
            # Calculate retry_after from oldest request in window
            if self._requests[identifier]:
                oldest_request = self._requests[identifier][0][0]
                retry_after = int((oldest_request + window_seconds) - current_time)
                return False, max(retry_after, 1)
            return False, window_seconds

        # Record this request
        self._requests[identifier].append((current_time, request_count + 1))
        return True, 0


# Global rate limiter instance
_rate_limiter = SimpleRateLimiter()


def rate_limit(max_requests: int = 3, window_seconds: int = 3600):
    """
    Decorator to rate limit an endpoint

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds (default: 1 hour)

    Usage:
        @router.post("/endpoint")
        @rate_limit(max_requests=3, window_seconds=3600)  # 3 per hour
        async def endpoint(request: Request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract request from args/kwargs
            request: Request = None

            # Try to find Request in args
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            # Try to find Request in kwargs
            if not request:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break

            if not request:
                # No request found, skip rate limiting
                return await func(*args, **kwargs)

            # Get identifier (prefer email from request body, fallback to IP)
            identifier = None

            # Try to get email from request body (for password reset)
            try:
                body = await request.body()
                if body:
                    import json
                    data = json.loads(body.decode())
                    identifier = data.get('email')

                    # Important: Reset the body for downstream processing
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
            except:
                pass

            # Fallback to IP address
            if not identifier:
                client_ip = request.client.host if request.client else "unknown"
                forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                identifier = forwarded_for or client_ip

            # Check rate limit
            allowed, retry_after = _rate_limiter.check_rate_limit(
                identifier=identifier,
                max_requests=max_requests,
                window_seconds=window_seconds
            )

            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Too many requests. Maximum {max_requests} requests per {window_seconds // 3600} hour(s).",
                        "retry_after": retry_after,
                        "limit": max_requests,
                        "window_seconds": window_seconds
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Window": str(window_seconds)
                    }
                )

            # Proceed with the request
            return await func(*args, **kwargs)

        return wrapper
    return decorator
