"""
Rate Limiting Middleware with Redis Backend
Implements per-user and per-IP rate limiting with sliding window algorithm
"""

import time
import hashlib
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from redis import asyncio as aioredis
from redis.exceptions import RedisError
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration for different endpoint tiers"""

    # Anonymous user limits
    ANONYMOUS_PER_MINUTE = 60
    ANONYMOUS_PER_HOUR = 1000

    # Authenticated user limits
    AUTHENTICATED_PER_MINUTE = 300
    AUTHENTICATED_PER_HOUR = 5000

    # Heavy endpoint limits (scraping, analysis)
    HEAVY_ENDPOINT_PER_MINUTE = 10
    HEAVY_ENDPOINT_PER_HOUR = 100

    # Time windows in seconds
    MINUTE_WINDOW = 60
    HOUR_WINDOW = 3600

    # Heavy endpoints pattern matching
    HEAVY_ENDPOINTS = [
        "/api/scraping",
        "/api/analysis",
    ]


class RateLimiter(BaseHTTPMiddleware):
    """
    Redis-based rate limiting middleware with sliding window algorithm

    Features:
    - Per-user quota tracking for authenticated users
    - Per-IP quota tracking for anonymous users
    - Configurable limits per endpoint
    - Rate limit headers (X-RateLimit-*)
    - Graceful degradation if Redis unavailable
    """

    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        enabled: bool = True,
        fail_open: bool = True
    ):
        """
        Initialize rate limiter

        Args:
            app: FastAPI application instance
            redis_url: Redis connection URL
            enabled: Enable/disable rate limiting
            fail_open: Allow requests if Redis is unavailable
        """
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.enabled = enabled
        self.fail_open = fail_open
        self.redis_client: Optional[aioredis.Redis] = None
        self._redis_available = True

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with rate limiting"""

        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Initialize Redis connection if needed
        if self.redis_client is None:
            await self._init_redis()

        # Get rate limit identifier (user ID or IP)
        identifier = self._get_identifier(request)

        # Determine endpoint tier
        is_heavy = self._is_heavy_endpoint(request.url.path)
        is_authenticated = self._is_authenticated(request)

        # Check rate limits
        try:
            allowed, limits_info = await self._check_rate_limit(
                identifier=identifier,
                is_authenticated=is_authenticated,
                is_heavy=is_heavy
            )

            if not allowed:
                return self._rate_limit_exceeded_response(limits_info)

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            self._add_rate_limit_headers(response, limits_info)

            return response

        except RedisError as e:
            logger.error(f"Redis error in rate limiter: {e}")
            self._redis_available = False

            if self.fail_open:
                logger.warning("Rate limiter failing open due to Redis error")
                return await call_next(request)
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate limiting service temporarily unavailable"
                )

    async def _init_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            await self.redis_client.ping()
            self._redis_available = True
            logger.info("Rate limiter Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis_available = False
            if not self.fail_open:
                raise

    def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting

        Returns user ID for authenticated users, IP hash for anonymous
        """
        # Try to get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if user:
            user_id = getattr(user, "id", None) or getattr(user, "sub", None)
            if user_id:
                return f"user:{user_id}"

        # Fall back to IP address for anonymous users
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        ip = forwarded_for or client_ip

        # Hash IP for privacy
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
        return f"ip:{ip_hash}"

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is from authenticated user"""
        user = getattr(request.state, "user", None)
        return user is not None

    def _is_heavy_endpoint(self, path: str) -> bool:
        """Check if endpoint is classified as heavy"""
        return any(path.startswith(heavy) for heavy in RateLimitConfig.HEAVY_ENDPOINTS)

    async def _check_rate_limit(
        self,
        identifier: str,
        is_authenticated: bool,
        is_heavy: bool
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using sliding window algorithm

        Returns:
            Tuple of (allowed, limits_info)
        """
        if not self._redis_available or self.redis_client is None:
            # Fail open if Redis unavailable
            return True, self._default_limits_info()

        current_time = int(time.time())

        # Determine limits
        if is_heavy:
            minute_limit = RateLimitConfig.HEAVY_ENDPOINT_PER_MINUTE
            hour_limit = RateLimitConfig.HEAVY_ENDPOINT_PER_HOUR
        elif is_authenticated:
            minute_limit = RateLimitConfig.AUTHENTICATED_PER_MINUTE
            hour_limit = RateLimitConfig.AUTHENTICATED_PER_HOUR
        else:
            minute_limit = RateLimitConfig.ANONYMOUS_PER_MINUTE
            hour_limit = RateLimitConfig.ANONYMOUS_PER_HOUR

        # Check minute window
        minute_key = f"ratelimit:{identifier}:minute:{current_time // 60}"
        minute_count = await self._increment_counter(
            minute_key,
            RateLimitConfig.MINUTE_WINDOW
        )

        # Check hour window
        hour_key = f"ratelimit:{identifier}:hour:{current_time // 3600}"
        hour_count = await self._increment_counter(
            hour_key,
            RateLimitConfig.HOUR_WINDOW
        )

        # Calculate remaining and reset times
        minute_remaining = max(0, minute_limit - minute_count)
        hour_remaining = max(0, hour_limit - hour_count)

        minute_reset = ((current_time // 60) + 1) * 60
        hour_reset = ((current_time // 3600) + 1) * 3600

        limits_info = {
            "limit_minute": minute_limit,
            "limit_hour": hour_limit,
            "remaining_minute": minute_remaining,
            "remaining_hour": hour_remaining,
            "reset_minute": minute_reset,
            "reset_hour": hour_reset,
            "current_minute": minute_count,
            "current_hour": hour_count
        }

        # Check if limits exceeded
        if minute_count > minute_limit or hour_count > hour_limit:
            limits_info["retry_after"] = min(
                minute_reset - current_time if minute_count > minute_limit else float('inf'),
                hour_reset - current_time if hour_count > hour_limit else float('inf')
            )
            return False, limits_info

        return True, limits_info

    async def _increment_counter(
        self,
        key: str,
        window: int
    ) -> int:
        """
        Increment counter with sliding window

        Args:
            key: Redis key for counter
            window: Time window in seconds

        Returns:
            Current count
        """
        if not self.redis_client:
            return 0

        try:
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = await pipe.execute()
            return int(results[0])
        except RedisError as e:
            logger.error(f"Redis error incrementing counter: {e}")
            self._redis_available = False
            raise

    def _default_limits_info(self) -> Dict[str, Any]:
        """Return default limits info when Redis unavailable"""
        return {
            "limit_minute": 0,
            "limit_hour": 0,
            "remaining_minute": 0,
            "remaining_hour": 0,
            "reset_minute": 0,
            "reset_hour": 0
        }

    def _rate_limit_exceeded_response(
        self,
        limits_info: Dict[str, Any]
    ) -> JSONResponse:
        """Return rate limit exceeded response"""
        retry_after = limits_info.get("retry_after", 60)

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after,
                "limits": {
                    "minute": {
                        "limit": limits_info["limit_minute"],
                        "remaining": limits_info["remaining_minute"],
                        "reset": limits_info["reset_minute"]
                    },
                    "hour": {
                        "limit": limits_info["limit_hour"],
                        "remaining": limits_info["remaining_hour"],
                        "reset": limits_info["reset_hour"]
                    }
                }
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit-Minute": str(limits_info["limit_minute"]),
                "X-RateLimit-Limit-Hour": str(limits_info["limit_hour"]),
                "X-RateLimit-Remaining-Minute": str(limits_info["remaining_minute"]),
                "X-RateLimit-Remaining-Hour": str(limits_info["remaining_hour"]),
                "X-RateLimit-Reset-Minute": str(limits_info["reset_minute"]),
                "X-RateLimit-Reset-Hour": str(limits_info["reset_hour"])
            }
        )

    def _add_rate_limit_headers(
        self,
        response: Response,
        limits_info: Dict[str, Any]
    ) -> None:
        """Add rate limit headers to successful response"""
        response.headers["X-RateLimit-Limit-Minute"] = str(limits_info["limit_minute"])
        response.headers["X-RateLimit-Limit-Hour"] = str(limits_info["limit_hour"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(limits_info["remaining_minute"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(limits_info["remaining_hour"])
        response.headers["X-RateLimit-Reset-Minute"] = str(limits_info["reset_minute"])
        response.headers["X-RateLimit-Reset-Hour"] = str(limits_info["reset_hour"])

    async def cleanup(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiter Redis connection closed")
