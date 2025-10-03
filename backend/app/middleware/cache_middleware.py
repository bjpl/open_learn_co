"""
HTTP Response Caching Middleware

Implements:
- Response caching with ETag support
- Cache-Control headers
- Conditional requests (304 Not Modified)
- Per-endpoint cache configuration
"""

import hashlib
import json
from typing import Callable, Optional, Set
from datetime import datetime, timedelta

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
from loguru import logger

from app.core.cache import cache_manager


class CacheMiddleware(BaseHTTPMiddleware):
    """
    HTTP response caching middleware with ETag support

    Features:
    - Automatic ETag generation from response body
    - Cache-Control header management
    - 304 Not Modified responses
    - Configurable per-endpoint caching
    - Bypass for authenticated requests
    """

    # Endpoints to cache (method, path_prefix)
    CACHEABLE_ENDPOINTS = {
        ("GET", "/api/scraping/sources"),
        ("GET", "/api/scraping/content"),
        ("GET", "/api/scraping/status"),
        ("GET", "/api/analysis/results"),
        ("GET", "/api/analysis/statistics"),
        ("GET", "/health"),
    }

    # Cache durations by endpoint pattern (seconds)
    CACHE_DURATIONS = {
        "/api/scraping/sources": 7200,  # 2 hours
        "/api/scraping/content": 1800,  # 30 minutes
        "/api/scraping/status": 300,  # 5 minutes
        "/api/analysis/results": 3600,  # 1 hour
        "/api/analysis/statistics": 600,  # 10 minutes
        "/health": 60,  # 1 minute
    }

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching logic"""

        # Skip if caching disabled
        if not self.enabled or not cache_manager.is_available:
            return await call_next(request)

        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Skip authenticated requests (for now)
        if self._is_authenticated(request):
            return await call_next(request)

        # Check if endpoint is cacheable
        cache_config = self._get_cache_config(request)
        if not cache_config:
            return await call_next(request)

        # Generate cache key from request
        cache_key = self._generate_cache_key(request)

        # Check for conditional request (If-None-Match)
        client_etag = request.headers.get("if-none-match")

        # Try to get cached response
        cached_data = await cache_manager.get(
            layer="http_response",
            identifier=cache_key
        )

        if cached_data:
            cached_etag = cached_data.get("etag")

            # Check if client has current version
            if client_etag and client_etag == cached_etag:
                logger.debug(f"HTTP Cache HIT (304): {request.url.path}")
                return Response(
                    status_code=304,
                    headers={
                        "ETag": cached_etag,
                        "Cache-Control": f"public, max-age={cache_config['duration']}"
                    }
                )

            # Return cached response
            logger.debug(f"HTTP Cache HIT (200): {request.url.path}")
            return Response(
                content=cached_data["body"],
                status_code=cached_data["status_code"],
                headers={
                    "Content-Type": cached_data["content_type"],
                    "ETag": cached_etag,
                    "Cache-Control": f"public, max-age={cache_config['duration']}",
                    "X-Cache": "HIT"
                }
            )

        # Cache miss - process request
        logger.debug(f"HTTP Cache MISS: {request.url.path}")
        response = await call_next(request)

        # Only cache successful responses
        if response.status_code == 200:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Generate ETag from body
            etag = self._generate_etag(body)

            # Cache response
            await cache_manager.set(
                layer="http_response",
                identifier=cache_key,
                value={
                    "body": body.decode("utf-8"),
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", "application/json"),
                    "etag": etag,
                    "cached_at": datetime.utcnow().isoformat()
                },
                ttl=cache_config["duration"]
            )

            # Return response with cache headers
            return Response(
                content=body,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    "ETag": etag,
                    "Cache-Control": f"public, max-age={cache_config['duration']}",
                    "X-Cache": "MISS"
                }
            )

        return response

    def _is_cacheable_endpoint(self, request: Request) -> bool:
        """Check if endpoint is cacheable"""
        method = request.method
        path = request.url.path

        for cache_method, cache_path in self.CACHEABLE_ENDPOINTS:
            if method == cache_method and path.startswith(cache_path):
                return True

        return False

    def _get_cache_config(self, request: Request) -> Optional[dict]:
        """Get cache configuration for endpoint"""
        if not self._is_cacheable_endpoint(request):
            return None

        path = request.url.path

        # Find matching cache duration
        for pattern, duration in self.CACHE_DURATIONS.items():
            if path.startswith(pattern):
                return {
                    "duration": duration,
                    "pattern": pattern
                }

        # Default cache duration
        return {
            "duration": 300,  # 5 minutes
            "pattern": path
        }

    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate cache key from request

        Includes:
        - Path
        - Query parameters
        - Accept header
        """
        components = [
            request.url.path,
            str(sorted(request.query_params.items())),
            request.headers.get("accept", "")
        ]

        key_str = "|".join(components)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _generate_etag(self, body: bytes) -> str:
        """Generate ETag from response body"""
        return f'"{hashlib.md5(body).hexdigest()}"'

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is authenticated"""
        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        return bool(auth_header)


async def invalidate_http_cache(pattern: str) -> int:
    """
    Invalidate HTTP response cache by pattern

    Args:
        pattern: Cache key pattern (e.g., "http_response:v1:*")

    Returns:
        Number of keys invalidated
    """
    return await cache_manager.delete_pattern(pattern)


async def invalidate_endpoint_cache(path_prefix: str) -> int:
    """
    Invalidate all cached responses for endpoint

    Args:
        path_prefix: Endpoint path prefix (e.g., "/api/scraping/content")

    Returns:
        Number of keys invalidated
    """
    # Note: This is simplified - in production, store reverse mapping
    # of path -> cache keys for efficient invalidation
    return await cache_manager.invalidate_layer("http_response")
