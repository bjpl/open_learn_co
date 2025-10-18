"""
Comprehensive Health Check Endpoints

Provides detailed health checks for all system dependencies:
- PostgreSQL database
- Redis cache
- Elasticsearch search
- File system access
- Overall system health

Includes Kubernetes readiness/liveness probes
"""

from fastapi import APIRouter, status
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import time
import os
import tempfile

from app.database.health import DatabaseHealthChecker
from app.core.cache import cache_manager
from app.search.elasticsearch_client import get_elasticsearch_client
from app.config.settings import settings

router = APIRouter()


class HealthStatus:
    """Health check status constants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"


async def check_database_health(timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check PostgreSQL database health

    Args:
        timeout: Maximum time to wait for health check

    Returns:
        Health check result with status and details
    """
    try:
        # Use asyncio timeout for health check
        health_result = await asyncio.wait_for(
            DatabaseHealthChecker.comprehensive_health_check(),
            timeout=timeout
        )

        return {
            "status": health_result.get("overall_status", HealthStatus.UNHEALTHY),
            "details": {
                "connection": health_result.get("checks", {}).get("connection", {}),
                "pool": health_result.get("checks", {}).get("connection_pool", {}),
                "query_performance_ms": health_result.get("checks", {}).get("query_performance", {}).get("query_time_ms"),
            },
            "response_time_ms": health_result.get("duration_ms", 0)
        }
    except asyncio.TimeoutError:
        return {
            "status": HealthStatus.TIMEOUT,
            "error": f"Database health check exceeded {timeout}s timeout",
            "response_time_ms": timeout * 1000
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": f"Database health check failed: {str(e)}",
            "response_time_ms": 0
        }


async def check_redis_health(timeout: float = 3.0) -> Dict[str, Any]:
    """
    Check Redis cache health

    Args:
        timeout: Maximum time to wait for health check

    Returns:
        Health check result with status and details
    """
    start_time = time.time()

    try:
        if not cache_manager.is_available:
            return {
                "status": HealthStatus.UNAVAILABLE,
                "error": "Redis connection not initialized",
                "response_time_ms": 0
            }

        # Test Redis with ping command using timeout
        redis_client = cache_manager._redis

        # Perform health check with timeout
        ping_result = await asyncio.wait_for(
            redis_client.ping(),
            timeout=timeout
        )

        response_time = (time.time() - start_time) * 1000

        if not ping_result:
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": "Redis ping failed",
                "response_time_ms": response_time
            }

        # Get cache statistics
        stats = await asyncio.wait_for(
            cache_manager.get_stats(),
            timeout=timeout
        )

        # Determine health status based on hit rate
        hit_rate = stats.get("hit_rate_percent", 0)
        if hit_rate < 50:
            cache_status = HealthStatus.DEGRADED
            warning = "Cache hit rate below 50%"
        else:
            cache_status = HealthStatus.HEALTHY
            warning = None

        return {
            "status": cache_status,
            "details": {
                "connected": True,
                "total_keys": stats.get("total_keys", 0),
                "memory_used_mb": stats.get("memory_used_mb", 0),
                "hit_rate_percent": hit_rate,
            },
            "warning": warning,
            "response_time_ms": round(response_time, 2)
        }

    except asyncio.TimeoutError:
        return {
            "status": HealthStatus.TIMEOUT,
            "error": f"Redis health check exceeded {timeout}s timeout",
            "response_time_ms": timeout * 1000
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": f"Redis health check failed: {str(e)}",
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }


async def check_elasticsearch_health(timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check Elasticsearch health

    Args:
        timeout: Maximum time to wait for health check

    Returns:
        Health check result with status and details
    """
    start_time = time.time()

    # Elasticsearch is optional - degraded if not configured
    if not settings.ELASTICSEARCH_ENABLED:
        return {
            "status": HealthStatus.DEGRADED,
            "message": "Elasticsearch not configured - search features limited",
            "response_time_ms": 0
        }

    try:
        es_client = await get_elasticsearch_client()

        # Perform health check with timeout
        health = await asyncio.wait_for(
            es_client.health_check(),
            timeout=timeout
        )

        response_time = (time.time() - start_time) * 1000

        # Determine status based on cluster health
        cluster_status = health.get("status", "").lower()
        if cluster_status == "green":
            es_status = HealthStatus.HEALTHY
        elif cluster_status == "yellow":
            es_status = HealthStatus.DEGRADED
        else:
            es_status = HealthStatus.UNHEALTHY

        return {
            "status": es_status,
            "details": {
                "cluster_status": cluster_status,
                "number_of_nodes": health.get("number_of_nodes", 0),
                "active_shards": health.get("active_shards", 0),
            },
            "response_time_ms": round(response_time, 2)
        }

    except asyncio.TimeoutError:
        return {
            "status": HealthStatus.TIMEOUT,
            "error": f"Elasticsearch health check exceeded {timeout}s timeout",
            "response_time_ms": timeout * 1000
        }
    except Exception as e:
        return {
            "status": HealthStatus.DEGRADED,
            "error": f"Elasticsearch unavailable: {str(e)}",
            "message": "Search features will be limited",
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }


async def check_filesystem_health() -> Dict[str, Any]:
    """
    Check file system access

    Returns:
        Health check result with status and details
    """
    start_time = time.time()

    try:
        # Test write access to temp directory
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            test_content = "health_check_test"
            tmp_file.write(test_content)
            tmp_path = tmp_file.name

        # Test read access
        with open(tmp_path, 'r') as tmp_file:
            content = tmp_file.read()
            if content != test_content:
                raise ValueError("File system read/write mismatch")

        # Clean up
        os.unlink(tmp_path)

        response_time = (time.time() - start_time) * 1000

        # Check disk space
        stat = os.statvfs(tempfile.gettempdir())
        free_space_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

        if free_space_gb < 1:
            fs_status = HealthStatus.DEGRADED
            warning = "Low disk space (<1GB free)"
        else:
            fs_status = HealthStatus.HEALTHY
            warning = None

        return {
            "status": fs_status,
            "details": {
                "writable": True,
                "readable": True,
                "free_space_gb": round(free_space_gb, 2),
            },
            "warning": warning,
            "response_time_ms": round(response_time, 2)
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": f"File system check failed: {str(e)}",
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }


async def calculate_overall_health(checks: Dict[str, Dict[str, Any]]) -> str:
    """
    Calculate overall system health from individual checks

    Args:
        checks: Dictionary of health check results

    Returns:
        Overall health status
    """
    statuses = [check.get("status") for check in checks.values()]

    # If any critical component is unhealthy, system is unhealthy
    critical_components = ["database", "filesystem"]
    for component in critical_components:
        if checks.get(component, {}).get("status") == HealthStatus.UNHEALTHY:
            return HealthStatus.UNHEALTHY
        if checks.get(component, {}).get("status") == HealthStatus.TIMEOUT:
            return HealthStatus.UNHEALTHY

    # If any component is degraded, system is degraded
    if HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED

    # If all healthy
    if all(s == HealthStatus.HEALTHY for s in statuses):
        return HealthStatus.HEALTHY

    # Default to degraded
    return HealthStatus.DEGRADED


@router.get("/health")
async def basic_health_check() -> Dict[str, str]:
    """
    Basic health check - always returns 200 if service is running

    Used for basic monitoring and load balancer health checks
    """
    return {"status": "ok", "service": "openlearn"}


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe

    Checks if service is ready to accept traffic
    Returns 200 if ready, 503 if not ready
    """
    start_time = time.time()

    # Perform quick checks on critical components
    checks = {
        "database": await check_database_health(timeout=3.0),
        "redis": await check_redis_health(timeout=2.0),
    }

    overall_status = await calculate_overall_health(checks)

    # Ready if database is healthy (Redis can be degraded)
    is_ready = checks["database"]["status"] in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    response = {
        "ready": is_ready,
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": round((time.time() - start_time) * 1000, 2)
    }

    # Return 503 if not ready
    if not is_ready:
        from fastapi import Response
        return Response(
            content=str(response),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )

    return response


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe

    Checks if service is alive and not deadlocked
    Returns 200 if alive, 503 if dead
    """
    # Simple check - if we can respond, we're alive
    return {
        "alive": True,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/comprehensive")
async def comprehensive_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for all system dependencies

    Checks:
    - PostgreSQL database
    - Redis cache
    - Elasticsearch search (optional)
    - File system access

    Returns detailed status for each component
    """
    start_time = time.time()

    # Run all health checks in parallel
    checks = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_elasticsearch_health(),
        check_filesystem_health(),
        return_exceptions=True
    )

    # Build health check results
    health_results = {
        "database": checks[0] if not isinstance(checks[0], Exception) else {
            "status": HealthStatus.UNHEALTHY,
            "error": str(checks[0])
        },
        "redis": checks[1] if not isinstance(checks[1], Exception) else {
            "status": HealthStatus.UNHEALTHY,
            "error": str(checks[1])
        },
        "elasticsearch": checks[2] if not isinstance(checks[2], Exception) else {
            "status": HealthStatus.DEGRADED,
            "error": str(checks[2])
        },
        "filesystem": checks[3] if not isinstance(checks[3], Exception) else {
            "status": HealthStatus.UNHEALTHY,
            "error": str(checks[3])
        }
    }

    overall_status = await calculate_overall_health(health_results)

    # Calculate health score (0-100)
    status_scores = {
        HealthStatus.HEALTHY: 100,
        HealthStatus.DEGRADED: 50,
        HealthStatus.UNAVAILABLE: 25,
        HealthStatus.TIMEOUT: 0,
        HealthStatus.UNHEALTHY: 0,
    }

    component_weights = {
        "database": 0.4,  # 40% weight
        "redis": 0.3,     # 30% weight
        "elasticsearch": 0.15,  # 15% weight (optional)
        "filesystem": 0.15,  # 15% weight
    }

    health_score = sum(
        status_scores.get(result["status"], 0) * component_weights.get(component, 0)
        for component, result in health_results.items()
    )

    total_response_time = (time.time() - start_time) * 1000

    return {
        "status": overall_status,
        "health_score": round(health_score, 2),
        "timestamp": datetime.utcnow().isoformat(),
        "checks": health_results,
        "response_time_ms": round(total_response_time, 2),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@router.get("/health/startup")
async def startup_check() -> Dict[str, Any]:
    """
    Kubernetes startup probe

    Checks if application has finished starting up
    More lenient timeout than readiness check
    """
    start_time = time.time()

    # Allow longer timeouts for startup
    checks = {
        "database": await check_database_health(timeout=10.0),
        "redis": await check_redis_health(timeout=5.0),
    }

    # Application is started if database connection works
    is_started = checks["database"]["status"] != HealthStatus.TIMEOUT

    return {
        "started": is_started,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": round((time.time() - start_time) * 1000, 2)
    }
