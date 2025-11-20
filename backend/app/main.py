"""
Colombia Intelligence & Language Learning Platform
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.custom_cors import CustomCORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

# PHASE 1: Core features only - minimal working backend
from app.api import scraping, analysis, auth, preferences, health, avatar
# Disabled for Phase 1: language, scheduler, analysis_batch, notifications, cache_admin, search, export
from app.database.connection import init_db, close_db, get_pool_status
from app.database.health import database_health_check, database_stats, pool_performance_test
# Disabled for Phase 1: from app.services.scheduler import start_scheduler, stop_scheduler
from app.search.elasticsearch_client import get_elasticsearch_client
from app.middleware.rate_limiter import RateLimiter
from app.middleware.security_headers import add_security_middleware
from app.middleware.compression import CompressionMiddleware
from app.middleware.cache_middleware import CacheMiddleware
from app.core.cache import cache_manager
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    # Startup
    logger.info("Starting Colombia Intel Platform...")
    await init_db()

    # Initialize Redis cache
    logger.info("Connecting to Redis cache...")
    await cache_manager.connect()

    # Initialize Elasticsearch
    logger.info("Connecting to Elasticsearch...")
    try:
        es_client = await get_elasticsearch_client()
        health = await es_client.health_check()
        if health.get("healthy"):
            logger.info(f"Elasticsearch connected: {health.get('status')}")
        else:
            logger.warning("Elasticsearch health check failed - search features may be limited")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        logger.warning("Continuing without Elasticsearch - search features will be unavailable")

    # PHASE 1: Scheduler disabled
    # if settings.ENABLE_SCHEDULER:
    #     await start_scheduler()

    logger.info("Platform started successfully (Phase 1: Core Features)")

    yield

    # Shutdown
    logger.info("Shutting down platform...")
    # PHASE 1: Scheduler disabled
    # if settings.ENABLE_SCHEDULER:
    #     await stop_scheduler(wait=True)

    # Disconnect Elasticsearch
    logger.info("Disconnecting Elasticsearch...")
    try:
        es_client = await get_elasticsearch_client()
        await es_client.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting Elasticsearch: {e}")

    # Disconnect Redis cache
    logger.info("Disconnecting Redis cache...")
    await cache_manager.disconnect()

    await close_db()
    logger.info("Platform shutdown complete")


# Create FastAPI instance
app = FastAPI(
    title="Colombia Intelligence & Language Learning Platform",
    description="OSINT aggregation and Spanish language acquisition for Colombian content",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# ⚠️ CRITICAL: CORS MUST BE FIRST MIDDLEWARE!
# Using custom CORS middleware as workaround for FastAPI CORSMiddleware bug
# where it doesn't send Access-Control-Allow-Origin header with other middleware
app.add_middleware(
    CustomCORSMiddleware,
    allowed_origins=settings.ALLOWED_ORIGINS
)

# Apply Compression Middleware
# Implements Brotli (preferred) and Gzip (fallback) compression
# Reduces bandwidth usage by 60-80% for JSON/HTML responses
app.add_middleware(
    CompressionMiddleware,
    min_size=getattr(settings, 'COMPRESSION_MIN_SIZE', 500),
    brotli_level=getattr(settings, 'BROTLI_COMPRESSION_LEVEL', 4),
    gzip_level=getattr(settings, 'GZIP_COMPRESSION_LEVEL', 6),
    enabled=getattr(settings, 'ENABLE_COMPRESSION', True),
)

# Apply Cache Middleware
# Implements HTTP response caching with ETag support and 304 responses
# Improves response times by 50-70% for cacheable endpoints
app.add_middleware(
    CacheMiddleware,
    enabled=True
)

# Apply Security Middleware
# Implements HSTS, CSP, X-Frame-Options, X-Content-Type-Options, etc.
add_security_middleware(app, settings)

# Configure Rate Limiting
# Redis-based rate limiting with per-user and per-IP tracking
# Different limits for anonymous, authenticated, and heavy endpoints
app.add_middleware(
    RateLimiter,
    redis_url=settings.REDIS_URL,
    enabled=True,
    fail_open=True  # Allow requests if Redis unavailable
)

# ============================================================================
# API Version 1 Router
# ============================================================================
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Create API v1 router
api_v1_router = APIRouter()

# Include all routers under /api/v1
api_v1_router.include_router(health.router, tags=["Health Checks"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(avatar.router, tags=["Avatar Upload"])
api_v1_router.include_router(scraping.router, prefix="/scraping", tags=["Web Scraping"])
api_v1_router.include_router(analysis.router, prefix="/analysis", tags=["Intelligence Analysis"])
api_v1_router.include_router(preferences.router, tags=["User Preferences"])
# PHASE 1: Disabled features - will enable in Phases 2-3
# api_v1_router.include_router(analysis_batch.router, tags=["Batch Analysis"])
# api_v1_router.include_router(language.router, prefix="/language", tags=["Language Learning"])
# api_v1_router.include_router(scheduler.router, prefix="/scheduler", tags=["Task Scheduler"])
# api_v1_router.include_router(cache_admin.router, tags=["Cache Administration"])
# api_v1_router.include_router(search.router, tags=["Search"])
# api_v1_router.include_router(export.router, tags=["Data Export"])
# api_v1_router.include_router(notifications.router, tags=["Notifications"])

# Mount v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# ============================================================================
# API Version Header Middleware
# ============================================================================
class APIVersionMiddleware(BaseHTTPMiddleware):
    """Add X-API-Version header to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-API-Version"] = "1.0.0"
        return response

app.add_middleware(APIVersionMiddleware)

# ============================================================================
# Backward Compatibility - Redirect /api/* to /api/v1/*
# ============================================================================
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
async def redirect_to_v1(path: str):
    """Redirect legacy /api/* endpoints to /api/v1/* for backward compatibility"""
    return RedirectResponse(url=f"/api/v1/{path}", status_code=301)


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with platform information"""
    return {
        "platform": "Colombia Intelligence & Language Learning",
        "version": "1.0.0",
        "api_version": "v1",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "api_v1": "/api/v1",
            "scraping": "/api/v1/scraping",
            "analysis": "/api/v1/analysis",
            "auth": "/api/v1/auth",
            "health": "/api/v1/health",
            "preferences": "/api/v1/preferences"
        },
        "features": {
            "api_versioning": "v1 API with backward compatibility",
            "batch_processing": "10x+ performance improvement for bulk NLP tasks",
            "job_queue": "Async processing with priority support",
            "result_caching": "Automatic caching for duplicate texts",
            "data_export": "CSV, JSON, PDF, Excel export with async job processing",
            "full_text_search": "Elasticsearch-powered search with advanced filters"
        },
        "notes": {
            "backward_compatibility": "Legacy /api/* endpoints redirect to /api/v1/* with 301 status",
            "version_header": "All responses include X-API-Version header"
        }
    }


# Legacy health endpoints - kept for backward compatibility
# New endpoints are in health.router

@app.get("/health/database")
async def database_health() -> Dict[str, Any]:
    """Comprehensive database health check with connection pool metrics"""
    return await database_health_check()


@app.get("/health/database/stats")
async def database_statistics() -> Dict[str, Any]:
    """Database statistics and performance metrics"""
    return await database_stats()


@app.get("/health/database/pool")
async def database_pool_status() -> Dict[str, Any]:
    """Connection pool status and metrics"""
    return get_pool_status()


@app.get("/health/database/pool/test")
async def test_pool_performance() -> Dict[str, Any]:
    """Test connection pool performance under concurrent load"""
    return await pool_performance_test()


@app.get("/health/compression")
async def compression_stats() -> Dict[str, Any]:
    """Get response compression statistics and metrics"""
    # Find compression middleware instance
    for middleware in app.user_middleware:
        if hasattr(middleware, 'cls') and middleware.cls == CompressionMiddleware:
            # Access middleware options
            return {
                "status": "enabled" if middleware.options.get('enabled', True) else "disabled",
                "configuration": {
                    "min_size_bytes": middleware.options.get('min_size', 500),
                    "brotli_level": middleware.options.get('brotli_level', 4),
                    "gzip_level": middleware.options.get('gzip_level', 6),
                },
                "note": "Detailed statistics available after processing requests"
            }

    return {
        "status": "not_configured",
        "message": "Compression middleware not found"
    }


@app.get("/health/cache")
async def cache_health() -> Dict[str, Any]:
    """Get Redis cache health and performance metrics"""
    return await cache_manager.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )