"""
Redis Cache Manager for OpenLearn Platform

Implements multi-layer caching with:
- L1: Query result caching (articles, sources, analytics)
- L2: API response caching (government APIs, news data)
- L3: Computed result caching (NLP analysis, sentiment scores)
- L4: Session caching (user preferences, tokens)

Performance Targets:
- Cache hit ratio: >80%
- Cache response time: <5ms
- API response time improvement: 50-70%
- Reduce database load: 60-80%
"""

import json
import hashlib
import asyncio
from typing import Any, Optional, Union, Callable, Dict, List
from datetime import timedelta
from functools import wraps

import redis.asyncio as aioredis
from redis.asyncio import Redis
from loguru import logger

from app.config.settings import settings


class CacheManager:
    """
    Redis-based cache manager with async operations

    Features:
    - Async Redis operations with connection pooling
    - Multiple cache layers with different TTLs
    - Cache stampede prevention
    - Cache versioning
    - Graceful degradation
    - Cache warming for popular data
    """

    # Cache layer configurations with TTLs
    CACHE_LAYERS = {
        # L1: Query Results (short-lived, frequently accessed)
        "article": {"ttl": 3600, "namespace": "article"},  # 1 hour
        "source": {"ttl": 7200, "namespace": "source"},  # 2 hours
        "analytics": {"ttl": 1800, "namespace": "analytics"},  # 30 minutes

        # L2: External API Responses (medium-lived)
        "api_government": {"ttl": 21600, "namespace": "api:gov"},  # 6 hours
        "api_news": {"ttl": 3600, "namespace": "api:news"},  # 1 hour

        # L3: Computed Results (long-lived, expensive to compute)
        "nlp_analysis": {"ttl": 86400, "namespace": "nlp"},  # 24 hours
        "sentiment": {"ttl": 86400, "namespace": "sentiment"},  # 24 hours
        "entities": {"ttl": 86400, "namespace": "entities"},  # 24 hours
        "topics": {"ttl": 86400, "namespace": "topics"},  # 24 hours

        # L4: Session Data (short-lived, user-specific)
        "session": {"ttl": 300, "namespace": "session"},  # 5 minutes
        "user_prefs": {"ttl": 1800, "namespace": "user"},  # 30 minutes
        "token": {"ttl": 1800, "namespace": "token"},  # 30 minutes
    }

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache manager with Redis connection"""
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[Redis] = None
        self._lock_prefix = "lock:"
        self._version = "v1"  # Cache version for invalidation

    async def connect(self) -> None:
        """Establish Redis connection with connection pool"""
        try:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            await self._redis.ping()
            logger.info("Redis cache connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Redis cache connection closed")

    @property
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self._redis is not None

    def _generate_key(self, layer: str, identifier: str, **params) -> str:
        """
        Generate cache key with namespace, version, and parameter hash

        Args:
            layer: Cache layer (article, nlp_analysis, etc.)
            identifier: Primary identifier (article_id, content_hash, etc.)
            **params: Additional parameters to include in key

        Returns:
            Cache key string
        """
        config = self.CACHE_LAYERS.get(layer, {"namespace": layer})
        namespace = config["namespace"]

        # Generate parameter hash if params exist
        if params:
            param_str = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            return f"{namespace}:{self._version}:{identifier}:{param_hash}"

        return f"{namespace}:{self._version}:{identifier}"

    def _get_ttl(self, layer: str) -> int:
        """Get TTL for cache layer"""
        return self.CACHE_LAYERS.get(layer, {}).get("ttl", 3600)

    async def get(
        self,
        layer: str,
        identifier: str,
        **params
    ) -> Optional[Any]:
        """
        Get cached value

        Args:
            layer: Cache layer
            identifier: Cache identifier
            **params: Additional parameters

        Returns:
            Cached value or None if not found/expired
        """
        if not self.is_available:
            return None

        try:
            key = self._generate_key(layer, identifier, **params)
            value = await self._redis.get(key)

            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)

            logger.debug(f"Cache MISS: {key}")
            return None

        except Exception as e:
            logger.warning(f"Cache get error for {layer}:{identifier}: {e}")
            return None

    async def set(
        self,
        layer: str,
        identifier: str,
        value: Any,
        ttl: Optional[int] = None,
        **params
    ) -> bool:
        """
        Set cached value

        Args:
            layer: Cache layer
            identifier: Cache identifier
            value: Value to cache (must be JSON serializable)
            ttl: Override default TTL
            **params: Additional parameters

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False

        try:
            key = self._generate_key(layer, identifier, **params)
            ttl = ttl or self._get_ttl(layer)

            serialized = json.dumps(value)
            await self._redis.setex(key, ttl, serialized)

            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.warning(f"Cache set error for {layer}:{identifier}: {e}")
            return False

    async def delete(
        self,
        layer: str,
        identifier: str,
        **params
    ) -> bool:
        """Delete cached value"""
        if not self.is_available:
            return False

        try:
            key = self._generate_key(layer, identifier, **params)
            await self._redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True

        except Exception as e:
            logger.warning(f"Cache delete error for {layer}:{identifier}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Redis key pattern (e.g., "article:v1:*")

        Returns:
            Number of keys deleted
        """
        if not self.is_available:
            return 0

        try:
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    deleted_count += await self._redis.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"Cache DELETE PATTERN: {pattern} ({deleted_count} keys)")
            return deleted_count

        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def invalidate_layer(self, layer: str) -> int:
        """Invalidate entire cache layer"""
        config = self.CACHE_LAYERS.get(layer, {"namespace": layer})
        namespace = config["namespace"]
        pattern = f"{namespace}:{self._version}:*"
        return await self.delete_pattern(pattern)

    async def exists(
        self,
        layer: str,
        identifier: str,
        **params
    ) -> bool:
        """Check if key exists in cache"""
        if not self.is_available:
            return False

        try:
            key = self._generate_key(layer, identifier, **params)
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error for {layer}:{identifier}: {e}")
            return False

    async def get_or_set(
        self,
        layer: str,
        identifier: str,
        fetch_func: Callable,
        ttl: Optional[int] = None,
        **params
    ) -> Any:
        """
        Get from cache or fetch and cache

        Implements cache-aside pattern with stampede prevention

        Args:
            layer: Cache layer
            identifier: Cache identifier
            fetch_func: Async function to fetch data if cache miss
            ttl: Override default TTL
            **params: Additional parameters

        Returns:
            Cached or fetched value
        """
        # Try cache first
        cached = await self.get(layer, identifier, **params)
        if cached is not None:
            return cached

        # Cache miss - use distributed lock to prevent stampede
        lock_key = f"{self._lock_prefix}{layer}:{identifier}"

        try:
            # Try to acquire lock
            lock_acquired = await self._redis.set(
                lock_key,
                "1",
                nx=True,
                ex=10  # Lock expires in 10 seconds
            ) if self.is_available else False

            if lock_acquired:
                # We got the lock - fetch data
                try:
                    value = await fetch_func()
                    await self.set(layer, identifier, value, ttl, **params)
                    return value
                finally:
                    # Release lock
                    if self.is_available:
                        await self._redis.delete(lock_key)
            else:
                # Another process is fetching - wait briefly and retry cache
                await asyncio.sleep(0.1)
                cached = await self.get(layer, identifier, **params)
                if cached is not None:
                    return cached

                # Still no cache - fetch directly (fallback)
                return await fetch_func()

        except Exception as e:
            logger.warning(f"Cache get_or_set error for {layer}:{identifier}: {e}")
            # Graceful degradation - fetch directly
            return await fetch_func()

    async def warm_cache(
        self,
        layer: str,
        items: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> int:
        """
        Warm cache with batch of items

        Args:
            layer: Cache layer
            items: List of dicts with 'identifier' and 'value' keys
            ttl: Override default TTL

        Returns:
            Number of items cached
        """
        if not self.is_available:
            return 0

        cached_count = 0
        ttl = ttl or self._get_ttl(layer)

        # Use pipeline for batch operations
        async with self._redis.pipeline() as pipe:
            for item in items:
                identifier = item.get("identifier")
                value = item.get("value")
                params = item.get("params", {})

                if identifier and value:
                    key = self._generate_key(layer, identifier, **params)
                    serialized = json.dumps(value)
                    pipe.setex(key, ttl, serialized)
                    cached_count += 1

            await pipe.execute()

        logger.info(f"Cache WARM: {layer} ({cached_count} items)")
        return cached_count

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_available:
            return {
                "status": "unavailable",
                "connected": False
            }

        try:
            info = await self._redis.info("stats")
            memory = await self._redis.info("memory")

            total_hits = int(info.get("keyspace_hits", 0))
            total_misses = int(info.get("keyspace_misses", 0))
            total_requests = total_hits + total_misses

            hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "status": "available",
                "connected": True,
                "total_keys": await self._redis.dbsize(),
                "memory_used_mb": round(int(memory.get("used_memory", 0)) / 1024 / 1024, 2),
                "memory_peak_mb": round(int(memory.get("used_memory_peak", 0)) / 1024 / 1024, 2),
                "hit_rate_percent": round(hit_rate, 2),
                "total_hits": total_hits,
                "total_misses": total_misses,
                "evicted_keys": int(info.get("evicted_keys", 0)),
                "expired_keys": int(info.get("expired_keys", 0))
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global cache manager instance
cache_manager = CacheManager()


def cached(
    layer: str,
    identifier_param: str = "id",
    ttl: Optional[int] = None,
    **cache_params
):
    """
    Decorator for caching function results

    Usage:
        @cached(layer="article", identifier_param="article_id")
        async def get_article(article_id: int):
            ...

    Args:
        layer: Cache layer to use
        identifier_param: Name of parameter to use as identifier
        ttl: Override default TTL
        **cache_params: Additional static cache parameters
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract identifier from kwargs
            identifier = kwargs.get(identifier_param)
            if not identifier:
                # Try to get from args (assume first arg after self)
                if len(args) > 0:
                    identifier = str(args[0])
                else:
                    # No identifier - skip cache
                    return await func(*args, **kwargs)

            identifier = str(identifier)

            # Create fetch function
            async def fetch_func():
                return await func(*args, **kwargs)

            # Get from cache or fetch
            return await cache_manager.get_or_set(
                layer=layer,
                identifier=identifier,
                fetch_func=fetch_func,
                ttl=ttl,
                **cache_params
            )

        return wrapper
    return decorator
