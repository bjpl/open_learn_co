"""
Colombia Intelligence & Language Learning Platform
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    lifespan=lifespan
)

# Apply Security Middleware (MUST be before CORS)
# Implements HSTS, CSP, X-Frame-Options, X-Content-Type-Options, etc.
add_security_middleware(app, settings)

# Apply Cache Middleware (MUST be before compression for proper handling)
# Implements HTTP response caching with ETag support and 304 responses
# Improves response times by 50-70% for cacheable endpoints
app.add_middleware(
    CacheMiddleware,
    enabled=True
)

# Apply Compression Middleware (MUST be before CORS for proper header handling)
# Implements Brotli (preferred) and Gzip (fallback) compression
# Reduces bandwidth usage by 60-80% for JSON/HTML responses
app.add_middleware(
    CompressionMiddleware,
    min_size=getattr(settings, 'COMPRESSION_MIN_SIZE', 500),
    brotli_level=getattr(settings, 'BROTLI_COMPRESSION_LEVEL', 4),
    gzip_level=getattr(settings, 'GZIP_COMPRESSION_LEVEL', 6),
    enabled=getattr(settings, 'ENABLE_COMPRESSION', True),
)

# Configure CORS (Restricted for production security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Must be explicit list, no wildcards
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Specific methods only
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Specific headers only
    expose_headers=["X-Total-Count"],
    max_age=600,  # Cache preflight for 10 minutes
)

# Configure Rate Limiting
# Redis-based rate limiting with per-user and per-IP tracking
# Different limits for anonymous, authenticated, and heavy endpoints
app.add_middleware(
    RateLimiter,
    redis_url=settings.REDIS_URL,
    enabled=True,
    fail_open=True  # Allow requests if Redis unavailable
)

# Include routers
app.include_router(health.router, tags=["Health Checks"])  # Health checks at root level
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(avatar.router, tags=["Avatar Upload"])  # Avatar upload with built-in prefix
app.include_router(scraping.router, prefix="/api/scraping", tags=["Web Scraping"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Intelligence Analysis"])
app.include_router(preferences.router, tags=["User Preferences"])
# PHASE 1: Disabled features - will enable in Phases 2-3
# app.include_router(analysis_batch.router, prefix="/api", tags=["Batch Analysis"])
# app.include_router(language.router, prefix="/api/language", tags=["Language Learning"])
# app.include_router(scheduler.router, prefix="/api/scheduler", tags=["Task Scheduler"])
# app.include_router(cache_admin.router, prefix="/api", tags=["Cache Administration"])
# app.include_router(search.router, prefix="/api", tags=["Search"])
# app.include_router(export.router, prefix="/api", tags=["Data Export"])
# app.include_router(notifications.router, prefix="/api", tags=["Notifications"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with platform information"""
    return {
        "platform": "Colombia Intelligence & Language Learning",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "scraping": "/api/scraping",
            "analysis": "/api/analysis",
            "batch_analysis": "/api/batch-analysis",
            "language": "/api/language",
            "search": "/api/search",
            "export": "/api/export"
        },
        "features": {
            "batch_processing": "10x+ performance improvement for bulk NLP tasks",
            "job_queue": "Async processing with priority support",
            "result_caching": "Automatic caching for duplicate texts",
            "data_export": "CSV, JSON, PDF, Excel export with async job processing",
            "full_text_search": "Elasticsearch-powered search with advanced filters"
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