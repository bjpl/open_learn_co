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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3006",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3006",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
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