"""
Monitoring Endpoints for Health Checks and Metrics

This module provides:
- Liveness probe (/health/live)
- Readiness probe (/health/ready)
- Startup probe (/health/startup)
- Prometheus metrics endpoint (/metrics)
"""

import asyncio
import sys
import psutil
import shutil
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch

from app.core.logging_config import get_logger
from app.core.metrics import get_metrics, get_content_type
from app.config.settings import settings


logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["monitoring"])


# ============================================================================
# Response Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    checks: Dict[str, Any] | None = None


class LivenessResponse(BaseModel):
    """Liveness probe response"""
    status: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness probe response"""
    status: str
    timestamp: str
    checks: Dict[str, bool]


class StartupResponse(BaseModel):
    """Startup probe response"""
    status: str
    timestamp: str
    initialized: bool


# ============================================================================
# Health Check Functions
# ============================================================================

# Connection pools (lazily initialized)
_db_engine = None
_redis_client = None
_es_client = None


def get_db_engine():
    """Get or create database engine"""
    global _db_engine
    if _db_engine is None:
        _db_engine = create_async_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=0,
        )
    return _db_engine


def get_redis_client():
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _redis_client


def get_es_client():
    """Get or create Elasticsearch client"""
    global _es_client
    if _es_client is None:
        _es_client = AsyncElasticsearch(
            [settings.ELASTICSEARCH_URL],
            request_timeout=5,
            max_retries=1,
        )
    return _es_client


async def check_database() -> Dict[str, Any]:
    """Check database connectivity with timeout"""
    try:
        engine = get_db_engine()

        # Use asyncio timeout to prevent hanging
        async with asyncio.timeout(5):
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()

        return {
            "healthy": True,
            "message": "PostgreSQL connection successful",
            "response_time_ms": None
        }
    except asyncio.TimeoutError:
        logger.error("Database health check timed out after 5 seconds")
        return {
            "healthy": False,
            "message": "Database connection timeout (5s)",
            "response_time_ms": None
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "healthy": False,
            "message": f"Database connection failed: {str(e)[:100]}",
            "response_time_ms": None
        }


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity with timeout"""
    try:
        client = get_redis_client()

        # Use asyncio timeout to prevent hanging
        async with asyncio.timeout(5):
            start = datetime.utcnow()
            await client.ping()
            response_time = (datetime.utcnow() - start).total_seconds() * 1000

        return {
            "healthy": True,
            "message": "Redis connection successful",
            "response_time_ms": round(response_time, 2)
        }
    except asyncio.TimeoutError:
        logger.error("Redis health check timed out after 5 seconds")
        return {
            "healthy": False,
            "message": "Redis connection timeout (5s)",
            "response_time_ms": None
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "healthy": False,
            "message": f"Redis connection failed: {str(e)[:100]}",
            "response_time_ms": None
        }


async def check_elasticsearch() -> Dict[str, Any]:
    """Check Elasticsearch connectivity with timeout"""
    try:
        client = get_es_client()

        # Use asyncio timeout to prevent hanging
        async with asyncio.timeout(5):
            start = datetime.utcnow()
            is_alive = await client.ping()
            response_time = (datetime.utcnow() - start).total_seconds() * 1000

        if is_alive:
            return {
                "healthy": True,
                "message": "Elasticsearch connection successful",
                "response_time_ms": round(response_time, 2)
            }
        else:
            return {
                "healthy": False,
                "message": "Elasticsearch ping returned False",
                "response_time_ms": None
            }
    except asyncio.TimeoutError:
        logger.error("Elasticsearch health check timed out after 5 seconds")
        return {
            "healthy": False,
            "message": "Elasticsearch connection timeout (5s)",
            "response_time_ms": None
        }
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return {
            "healthy": False,
            "message": f"Elasticsearch connection failed: {str(e)[:100]}",
            "response_time_ms": None
        }


def check_disk_space() -> Dict[str, Any]:
    """Check disk space availability"""
    try:
        # Check root filesystem
        disk_usage = shutil.disk_usage("/")
        total_gb = disk_usage.total / (1024 ** 3)
        used_gb = disk_usage.used / (1024 ** 3)
        free_gb = disk_usage.free / (1024 ** 3)
        percent_used = (disk_usage.used / disk_usage.total) * 100

        # Warning threshold: 85%, Critical: 95%
        if percent_used >= 95:
            status_msg = "CRITICAL: Less than 5% disk space remaining"
            healthy = False
        elif percent_used >= 85:
            status_msg = "WARNING: Less than 15% disk space remaining"
            healthy = False
        else:
            status_msg = "Disk space sufficient"
            healthy = True

        return {
            "healthy": healthy,
            "message": status_msg,
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "percent_used": round(percent_used, 2)
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return {
            "healthy": False,
            "message": f"Disk space check failed: {str(e)[:100]}",
            "total_gb": None,
            "used_gb": None,
            "free_gb": None,
            "percent_used": None
        }


def check_memory() -> Dict[str, Any]:
    """Check memory usage"""
    try:
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        available_gb = mem.available / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)
        percent_used = mem.percent

        # Warning threshold: 85%, Critical: 95%
        if percent_used >= 95:
            status_msg = "CRITICAL: Less than 5% memory available"
            healthy = False
        elif percent_used >= 85:
            status_msg = "WARNING: Less than 15% memory available"
            healthy = False
        else:
            status_msg = "Memory usage normal"
            healthy = True

        return {
            "healthy": healthy,
            "message": status_msg,
            "total_gb": round(total_gb, 2),
            "available_gb": round(available_gb, 2),
            "used_gb": round(used_gb, 2),
            "percent_used": round(percent_used, 2)
        }
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        return {
            "healthy": False,
            "message": f"Memory check failed: {str(e)[:100]}",
            "total_gb": None,
            "available_gb": None,
            "used_gb": None,
            "percent_used": None
        }


# ============================================================================
# Liveness Probe
# ============================================================================

@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Indicates if the application is running"
)
async def liveness_probe():
    """
    Liveness probe for Kubernetes

    Returns 200 if the application is running.
    This should only fail if the application is deadlocked or crashed.
    """
    return LivenessResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )


# ============================================================================
# Readiness Probe
# ============================================================================

@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Indicates if the application is ready to serve traffic"
)
async def readiness_probe(response: Response):
    """
    Readiness probe for Kubernetes

    Returns 200 if the application is ready to serve traffic.
    Checks all critical dependencies.
    """
    db_check = await check_database()
    redis_check = await check_redis()
    es_check = await check_elasticsearch()

    checks = {
        "database": db_check["healthy"],
        "redis": redis_check["healthy"],
        "elasticsearch": es_check["healthy"],
    }

    all_healthy = all(checks.values())

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            checks=checks
        )

    return ReadinessResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )


# ============================================================================
# Startup Probe
# ============================================================================

# Global startup state
_startup_complete = False


def mark_startup_complete():
    """Mark startup as complete"""
    global _startup_complete
    _startup_complete = True


@router.get(
    "/startup",
    response_model=StartupResponse,
    summary="Startup probe",
    description="Indicates if the application has completed startup"
)
async def startup_probe(response: Response):
    """
    Startup probe for Kubernetes

    Returns 200 once the application has completed startup initialization.
    Used to delay liveness and readiness probes during slow startup.
    """
    if not _startup_complete:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return StartupResponse(
            status="starting",
            timestamp=datetime.utcnow().isoformat(),
            initialized=False
        )

    return StartupResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        initialized=True
    )


# ============================================================================
# Detailed Health Check
# ============================================================================

@router.get(
    "",
    response_model=HealthResponse,
    summary="Detailed health check",
    description="Detailed health status including all checks"
)
async def health_check():
    """
    Detailed health check with all components

    Returns comprehensive health information including:
    - Application status
    - Database connectivity
    - Cache connectivity
    - Search engine connectivity
    - System information (disk, memory)
    """
    # Run all checks
    db_check = await check_database()
    redis_check = await check_redis()
    es_check = await check_elasticsearch()
    disk_check = check_disk_space()
    memory_check = check_memory()

    checks = {
        "database": db_check,
        "redis": redis_check,
        "elasticsearch": es_check,
        "disk": disk_check,
        "memory": memory_check,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "startup_complete": _startup_complete,
    }

    # Determine overall health status
    component_health = [
        db_check["healthy"],
        redis_check["healthy"],
        es_check["healthy"],
        disk_check["healthy"],
        memory_check["healthy"],
    ]

    all_healthy = all(component_health)
    any_unhealthy = not all(component_health)

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )


# ============================================================================
# Metrics Endpoint
# ============================================================================

metrics_router = APIRouter(tags=["monitoring"])


@metrics_router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Prometheus metrics in exposition format"
)
async def metrics_endpoint():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus exposition format for scraping.
    """
    metrics_data = get_metrics()

    return Response(
        content=metrics_data,
        media_type=get_content_type()
    )
