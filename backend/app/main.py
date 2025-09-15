"""
Colombia Intelligence & Language Learning Platform
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from app.api import scraping, analysis, language, auth
from app.database.connection import init_db, close_db
from app.services.scheduler import start_scheduler
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
    if settings.ENABLE_SCHEDULER:
        await start_scheduler()
    logger.info("Platform started successfully")

    yield

    # Shutdown
    logger.info("Shutting down platform...")
    await close_db()
    logger.info("Platform shutdown complete")


# Create FastAPI instance
app = FastAPI(
    title="Colombia Intelligence & Language Learning Platform",
    description="OSINT aggregation and Spanish language acquisition for Colombian content",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["Web Scraping"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Intelligence Analysis"])
app.include_router(language.router, prefix="/api/language", tags=["Language Learning"])


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
            "language": "/api/language"
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )