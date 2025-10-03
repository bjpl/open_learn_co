"""
Cache Administration API

Provides endpoints for:
- Cache health monitoring
- Cache statistics
- Manual cache invalidation
- Cache warming
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.core.cache import cache_manager
from app.core.metrics import metrics_collector
from app.services.cache_service import cache_service
from app.config.settings import settings


router = APIRouter(prefix="/cache", tags=["Cache Administration"])


class CacheInvalidateRequest(BaseModel):
    """Request model for cache invalidation"""
    layer: str = Field(..., description="Cache layer to invalidate")
    identifier: Optional[str] = Field(None, description="Specific identifier to invalidate")
    pattern: Optional[str] = Field(None, description="Pattern for bulk invalidation")


class CacheWarmRequest(BaseModel):
    """Request model for cache warming"""
    layer: str = Field(..., description="Cache layer to warm")
    items: List[Dict[str, Any]] = Field(..., description="Items to cache")
    ttl: Optional[int] = Field(None, description="Override TTL in seconds")


@router.get("/health")
async def get_cache_health() -> Dict[str, Any]:
    """
    Get comprehensive cache health metrics

    Returns:
    - Connection status
    - Hit rate statistics
    - Memory usage
    - Performance metrics
    - Health score and recommendations
    """
    return await cache_service.get_cache_health()


@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get detailed cache statistics

    Returns:
    - Total keys
    - Memory usage
    - Hit/miss ratios
    - Eviction statistics
    """
    stats = await cache_manager.get_stats()

    # Add layer breakdown
    layer_info = {}
    for layer, config in cache_manager.CACHE_LAYERS.items():
        layer_info[layer] = {
            "namespace": config["namespace"],
            "ttl_seconds": config["ttl"],
            "ttl_human": f"{config['ttl'] // 3600}h {(config['ttl'] % 3600) // 60}m" if config['ttl'] >= 3600 else f"{config['ttl'] // 60}m"
        }

    return {
        **stats,
        "layers": layer_info,
        "performance_targets": {
            "hit_rate_target_percent": 80,
            "response_time_target_ms": 5,
            "current_hit_rate_percent": stats.get("hit_rate_percent", 0),
            "target_met": stats.get("hit_rate_percent", 0) >= 80
        }
    }


@router.get("/layers")
async def list_cache_layers() -> Dict[str, Any]:
    """
    List all configured cache layers

    Returns layer configurations and descriptions
    """
    layers = {}

    for layer, config in cache_manager.CACHE_LAYERS.items():
        # Categorize layers
        if layer in ["article", "source", "analytics"]:
            category = "Query Results (L1)"
            description = "Short-lived, frequently accessed data"
        elif layer in ["api_government", "api_news"]:
            category = "External API Responses (L2)"
            description = "Medium-lived external API data"
        elif layer in ["nlp_analysis", "sentiment", "entities", "topics"]:
            category = "Computed Results (L3)"
            description = "Long-lived, expensive computations"
        elif layer in ["session", "user_prefs", "token"]:
            category = "Session Data (L4)"
            description = "Short-lived user-specific data"
        else:
            category = "Other"
            description = "Custom cache layer"

        layers[layer] = {
            "category": category,
            "description": description,
            "namespace": config["namespace"],
            "ttl_seconds": config["ttl"],
            "ttl_human": f"{config['ttl'] // 3600}h {(config['ttl'] % 3600) // 60}m" if config['ttl'] >= 3600 else f"{config['ttl'] // 60}m"
        }

    return {
        "total_layers": len(layers),
        "layers": layers
    }


@router.post("/invalidate")
async def invalidate_cache(request: CacheInvalidateRequest) -> Dict[str, Any]:
    """
    Invalidate cache entries

    Supports:
    - Single key invalidation (provide layer + identifier)
    - Pattern invalidation (provide layer + pattern)
    - Layer invalidation (provide layer only)
    """
    if request.pattern:
        # Pattern-based invalidation
        count = await cache_manager.delete_pattern(request.pattern)
        return {
            "status": "success",
            "operation": "pattern_invalidation",
            "pattern": request.pattern,
            "keys_invalidated": count
        }

    if request.identifier:
        # Single key invalidation
        success = await cache_manager.delete(request.layer, request.identifier)
        return {
            "status": "success" if success else "failed",
            "operation": "single_invalidation",
            "layer": request.layer,
            "identifier": request.identifier
        }

    # Layer invalidation
    count = await cache_manager.invalidate_layer(request.layer)
    return {
        "status": "success",
        "operation": "layer_invalidation",
        "layer": request.layer,
        "keys_invalidated": count
    }


@router.post("/invalidate/article/{article_id}")
async def invalidate_article_cache(article_id: int) -> Dict[str, Any]:
    """
    Invalidate all cache related to an article

    Cascade invalidation includes:
    - Article details
    - Article lists
    - Analytics
    - NLP analysis
    """
    results = await cache_service.invalidate_article_cache(article_id)
    return {
        "status": "success",
        "article_id": article_id,
        "invalidated": results,
        "total_keys": sum(results.values())
    }


@router.post("/invalidate/source/{source_name}")
async def invalidate_source_cache(source_name: str) -> Dict[str, Any]:
    """
    Invalidate all cache related to a source

    Includes:
    - Source configuration
    - Articles from source
    - HTTP responses
    """
    results = await cache_service.invalidate_source_cache(source_name)
    return {
        "status": "success",
        "source_name": source_name,
        "invalidated": results,
        "total_keys": sum(results.values())
    }


@router.post("/invalidate/all")
async def invalidate_all_cache() -> Dict[str, Any]:
    """
    Nuclear option: Invalidate ALL cache layers

    WARNING: This will clear the entire cache!
    Use with caution - causes temporary performance degradation
    """
    results = await cache_service.invalidate_all()
    return {
        "status": "success",
        "warning": "All cache layers invalidated",
        "invalidated": results,
        "total_keys": sum(results.values())
    }


@router.post("/warm")
async def warm_cache(request: CacheWarmRequest) -> Dict[str, Any]:
    """
    Warm cache with batch of items

    Preloads popular data into cache to improve hit rates
    """
    count = await cache_manager.warm_cache(
        layer=request.layer,
        items=request.items,
        ttl=request.ttl
    )

    return {
        "status": "success",
        "layer": request.layer,
        "items_cached": count,
        "ttl_seconds": request.ttl or cache_manager._get_ttl(request.layer)
    }


@router.get("/metrics")
async def get_cache_metrics() -> Dict[str, Any]:
    """
    Get cache performance metrics

    Returns:
    - Hit/miss ratios
    - Response times
    - Memory usage
    - Performance improvements
    """
    cache_metrics = metrics_collector.get_cache_metrics()
    performance_metrics = metrics_collector.get_performance_metrics()
    uptime = metrics_collector.get_uptime()

    return {
        "cache": cache_metrics.to_dict(),
        "performance": performance_metrics.to_dict(),
        "uptime": uptime
    }


@router.get("/key/{layer}/{identifier}")
async def get_cached_value(
    layer: str,
    identifier: str
) -> Dict[str, Any]:
    """
    Get cached value by layer and identifier

    Useful for debugging and inspecting cache contents
    """
    value = await cache_manager.get(layer, identifier)

    if value is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached value found for {layer}:{identifier}"
        )

    return {
        "layer": layer,
        "identifier": identifier,
        "value": value,
        "exists": True
    }


@router.get("/exists/{layer}/{identifier}")
async def check_cache_exists(
    layer: str,
    identifier: str
) -> Dict[str, Any]:
    """
    Check if key exists in cache
    """
    exists = await cache_manager.exists(layer, identifier)

    return {
        "layer": layer,
        "identifier": identifier,
        "exists": exists
    }


@router.get("/performance/comparison")
async def get_performance_comparison() -> Dict[str, Any]:
    """
    Compare cached vs non-cached performance

    Returns estimated performance improvements
    """
    stats = await cache_manager.get_stats()
    hit_rate = stats.get("hit_rate_percent", 0)

    # Estimate performance improvements based on hit rate
    # Assumptions:
    # - Cache response time: 5ms
    # - DB query response time: 100ms
    # - API call response time: 500ms

    cache_time_ms = 5
    db_time_ms = 100
    api_time_ms = 500

    # Calculate weighted average response time
    avg_response_cached = cache_time_ms
    avg_response_uncached = (db_time_ms * 0.7) + (api_time_ms * 0.3)  # 70% DB, 30% API

    # Calculate improvement with current hit rate
    current_avg = (
        (hit_rate / 100) * avg_response_cached +
        ((100 - hit_rate) / 100) * avg_response_uncached
    )

    improvement_percent = (
        ((avg_response_uncached - current_avg) / avg_response_uncached) * 100
    )

    return {
        "cache_hit_rate_percent": round(hit_rate, 2),
        "cache_response_time_ms": cache_time_ms,
        "database_response_time_ms": db_time_ms,
        "api_response_time_ms": api_time_ms,
        "current_avg_response_time_ms": round(current_avg, 2),
        "uncached_avg_response_time_ms": round(avg_response_uncached, 2),
        "performance_improvement_percent": round(improvement_percent, 2),
        "estimated_speedup": round(avg_response_uncached / current_avg, 2) if current_avg > 0 else 0,
        "targets": {
            "hit_rate_target_percent": 80,
            "response_time_target_ms": 50,
            "improvement_target_percent": 60,
            "hit_rate_met": hit_rate >= 80,
            "improvement_met": improvement_percent >= 60
        }
    }
