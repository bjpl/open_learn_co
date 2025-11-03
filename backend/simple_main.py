"""
Simple FastAPI server for OpenLearn Colombia
Development version without scrapers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
import os
import sys

# Add app directory to path for importing middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from middleware.security_headers import SecurityHeadersMiddleware
    SECURITY_HEADERS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  SecurityHeadersMiddleware not found. Security headers will not be added.")
    SECURITY_HEADERS_AVAILABLE = False

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
    logger.info("Starting OpenLearn Colombia Backend...")
    logger.info("Backend started successfully")

    yield

    # Shutdown
    logger.info("Shutting down backend...")
    logger.info("Backend shutdown complete")


# Create FastAPI instance
app = FastAPI(
    title="OpenLearn Colombia Backend API",
    description="Language learning platform for Colombian Spanish",
    version="1.0.0",
    lifespan=lifespan
)

# Add Security Headers Middleware (HSTS, CSP, X-Frame-Options, etc.)
# This protects against XSS, clickjacking, and other attacks
if SECURITY_HEADERS_AVAILABLE:
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("✅ Security headers middleware enabled")
else:
    logger.warning("⚠️  Security headers middleware not available - install requirements")

# ⚠️  SECURITY NOTE: CORS configuration
# In production, NEVER use wildcard ("*")! Specify exact domains only.
# Read more: docs/SECURITY.md

# Get allowed origins from environment variable or use defaults for development
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3006,http://127.0.0.1:3000,http://127.0.0.1:3006"
).split(",")

# Remove wildcard in production - it's a security risk!
# Only use wildcard in local development
if os.getenv("ENVIRONMENT") == "production" and "*" in ALLOWED_ORIGINS:
    logger.error("⚠️  SECURITY ERROR: Wildcard CORS is NOT allowed in production!")
    logger.error("Set CORS_ALLOWED_ORIGINS environment variable to specific domains.")
    raise ValueError("Wildcard CORS configuration is insecure for production")

# Configure CORS with environment-based origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with platform information"""
    return {
        "platform": "OpenLearn Colombia",
        "version": "1.0.0",
        "status": "operational",
        "message": "Colombian Spanish Learning Platform API",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api"
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "openlearn-colombia-backend"}


@app.get("/api/status")
async def api_status() -> Dict[str, Any]:
    """API status endpoint"""
    return {
        "api_status": "running",
        "database": "sqlite_ready",
        "cors": "enabled",
        "ports": {
            "backend": 8000,
            "frontend": 3006
        },
        "features": [
            "Content scraping",
            "Language analysis",
            "User progress tracking",
            "Colombian Spanish learning",
            "News aggregation",
            "Intelligence analysis"
        ],
        "endpoints": {
            "root": "/",
            "health": "/health",
            "docs": "/docs",
            "api_status": "/api/status",
            "api_test": "/api/test"
        }
    }


@app.get("/api/test")
async def test_endpoint() -> Dict[str, str]:
    """Test endpoint for frontend connectivity"""
    return {
        "message": "Backend connection successful!",
        "cors": "enabled",
        "timestamp": "2024-09-15"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )