"""
Cache Service for Cache Invalidation and Management

Provides:
- Intelligent cache invalidation strategies
- Pattern-based invalidation
- Time-based expiration
- Manual cache clearing
- Cache warming utilities
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.core.cache import cache_manager


class CacheInvalidationService:
    """
    Service for managing cache invalidation strategies

    Implements various invalidation patterns:
    - Direct invalidation (specific key)
    - Pattern invalidation (wildcard)
    - Cascade invalidation (related keys)
    - Time-based expiration
    """

    @staticmethod
    async def invalidate_article_cache(article_id: int) -> Dict[str, int]:
        """
        Invalidate all cache entries related to an article

        Cascade invalidation:
        - Article details
        - Article list (containing this article)
        - Related analytics
        - NLP analysis results
        """
        results = {}

        # Direct article cache
        results["article_detail"] = 1 if await cache_manager.delete(
            "article",
            str(article_id)
        ) else 0

        # Article lists (invalidate all to ensure consistency)
        results["article_lists"] = await cache_manager.invalidate_layer("article")

        # Related analytics
        results["analytics"] = await cache_manager.delete_pattern(
            f"analytics:v1:*article_{article_id}*"
        )

        # NLP analysis
        results["nlp_analysis"] = await cache_manager.delete_pattern(
            f"nlp:v1:*{article_id}*"
        )

        logger.info(f"Invalidated article cache for ID {article_id}: {results}")
        return results

    @staticmethod
    async def invalidate_source_cache(source_name: str) -> Dict[str, int]:
        """
        Invalidate cache for a specific source

        Args:
            source_name: Source identifier (e.g., "El Tiempo")
        """
        results = {}

        # Source configuration cache
        results["source_config"] = await cache_manager.delete_pattern(
            f"source:v1:*{source_name}*"
        )

        # Articles from this source
        results["source_articles"] = await cache_manager.delete_pattern(
            f"article:v1:*source_{source_name}*"
        )

        # HTTP responses for this source
        results["http_responses"] = await cache_manager.delete_pattern(
            f"http_response:v1:*source={source_name}*"
        )

        logger.info(f"Invalidated source cache for '{source_name}': {results}")
        return results

    @staticmethod
    async def invalidate_nlp_cache(content_hash: str) -> int:
        """
        Invalidate NLP analysis cache for specific content

        Args:
            content_hash: Hash of analyzed content
        """
        count = await cache_manager.delete_pattern(
            f"nlp:v1:{content_hash}*"
        )

        # Also invalidate related sentiment and entities
        count += await cache_manager.delete(
            "sentiment",
            content_hash
        )
        count += await cache_manager.delete(
            "entities",
            content_hash
        )

        logger.info(f"Invalidated NLP cache for hash {content_hash}: {count} keys")
        return count

    @staticmethod
    async def invalidate_user_cache(user_id: int) -> Dict[str, int]:
        """
        Invalidate all user-specific cache

        Args:
            user_id: User identifier
        """
        results = {}

        # User session
        results["session"] = 1 if await cache_manager.delete(
            "session",
            str(user_id)
        ) else 0

        # User preferences
        results["preferences"] = 1 if await cache_manager.delete(
            "user_prefs",
            str(user_id)
        ) else 0

        # User tokens
        results["tokens"] = await cache_manager.delete_pattern(
            f"token:v1:*{user_id}*"
        )

        logger.info(f"Invalidated user cache for ID {user_id}: {results}")
        return results

    @staticmethod
    async def invalidate_api_cache(
        api_type: str,
        endpoint: Optional[str] = None
    ) -> int:
        """
        Invalidate external API response cache

        Args:
            api_type: API type (government, news, etc.)
            endpoint: Specific endpoint or None for all
        """
        if endpoint:
            pattern = f"api:{api_type}:v1:*{endpoint}*"
        else:
            pattern = f"api:{api_type}:v1:*"

        count = await cache_manager.delete_pattern(pattern)
        logger.info(f"Invalidated {api_type} API cache: {count} keys")
        return count

    @staticmethod
    async def clear_expired_cache() -> Dict[str, int]:
        """
        Clear all expired cache entries

        Note: Redis handles expiration automatically, but this can
        be used for manual cleanup or reporting
        """
        # Redis auto-expires keys, so this is mainly for stats
        stats = await cache_manager.get_stats()

        return {
            "expired_keys": stats.get("expired_keys", 0),
            "evicted_keys": stats.get("evicted_keys", 0)
        }

    @staticmethod
    async def warm_article_cache(articles: List[Dict[str, Any]]) -> int:
        """
        Warm cache with popular articles

        Args:
            articles: List of article data dictionaries
        """
        items = [
            {
                "identifier": str(article["id"]),
                "value": article
            }
            for article in articles
        ]

        count = await cache_manager.warm_cache(
            layer="article",
            items=items,
            ttl=3600  # 1 hour for warm cache
        )

        logger.info(f"Warmed article cache with {count} items")
        return count

    @staticmethod
    async def warm_source_cache(sources: List[Dict[str, Any]]) -> int:
        """
        Warm cache with source configurations

        Args:
            sources: List of source configuration dictionaries
        """
        items = [
            {
                "identifier": source["name"],
                "value": source
            }
            for source in sources
        ]

        count = await cache_manager.warm_cache(
            layer="source",
            items=items,
            ttl=7200  # 2 hours for source config
        )

        logger.info(f"Warmed source cache with {count} items")
        return count

    @staticmethod
    async def invalidate_all() -> Dict[str, int]:
        """
        Nuclear option: Clear all cache layers

        Use with caution!
        """
        results = {}

        for layer in cache_manager.CACHE_LAYERS.keys():
            results[layer] = await cache_manager.invalidate_layer(layer)

        logger.warning(f"Invalidated ALL cache layers: {results}")
        return results

    @staticmethod
    async def get_cache_health() -> Dict[str, Any]:
        """
        Get cache health metrics

        Returns comprehensive cache statistics
        """
        stats = await cache_manager.get_stats()

        # Calculate health score based on hit rate and memory usage
        hit_rate = stats.get("hit_rate_percent", 0)
        memory_used = stats.get("memory_used_mb", 0)
        memory_peak = stats.get("memory_peak_mb", 1)

        memory_ratio = memory_used / memory_peak if memory_peak > 0 else 0

        # Health score (0-100)
        health_score = (
            (hit_rate * 0.6) +  # 60% weight on hit rate
            ((1 - memory_ratio) * 40)  # 40% weight on memory availability
        )

        return {
            **stats,
            "health_score": round(health_score, 2),
            "health_status": (
                "excellent" if health_score >= 80 else
                "good" if health_score >= 60 else
                "fair" if health_score >= 40 else
                "poor"
            ),
            "recommendations": CacheInvalidationService._get_recommendations(stats)
        }

    @staticmethod
    def _get_recommendations(stats: Dict[str, Any]) -> List[str]:
        """Generate cache optimization recommendations"""
        recommendations = []

        hit_rate = stats.get("hit_rate_percent", 0)
        if hit_rate < 80:
            recommendations.append(
                f"Low cache hit rate ({hit_rate:.1f}%). "
                "Consider warming cache with popular data."
            )

        evicted = stats.get("evicted_keys", 0)
        if evicted > 1000:
            recommendations.append(
                f"High eviction rate ({evicted} keys). "
                "Consider increasing Redis memory limit."
            )

        memory_used = stats.get("memory_used_mb", 0)
        if memory_used > 1000:
            recommendations.append(
                f"High memory usage ({memory_used:.1f} MB). "
                "Consider reducing TTLs or implementing LRU eviction."
            )

        return recommendations


# Global service instance
cache_service = CacheInvalidationService()
