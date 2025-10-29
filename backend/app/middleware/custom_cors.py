"""
Custom CORS Middleware - Workaround for FastAPI CORSMiddleware bug

This middleware manually adds Access-Control-Allow-Origin header
because FastAPI's built-in CORSMiddleware isn't sending it properly.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class CustomCORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware that manually adds Access-Control-Allow-Origin header.

    This is a workaround for issues with FastAPI's CORSMiddleware not
    sending the Allow-Origin header when other middleware is present.
    """

    def __init__(self, app, allowed_origins: list[str]):
        super().__init__(app)
        self.allowed_origins = allowed_origins
        logger.info(f"Custom CORS Middleware initialized with origins: {allowed_origins}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add CORS headers to response"""

        # Get the origin from request
        origin = request.headers.get("origin")
        logger.info(f"🔍 CORS dispatch called - Method: {request.method}, Origin: {origin}, Path: {request.url.path}")

        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            logger.info(f"🚀 Handling OPTIONS preflight for origin: {origin}")
            response = Response(status_code=200)
            if origin and origin in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "600"
                logger.info(f"✅ Added OPTIONS CORS headers for: {origin}")
            return response

        # Process regular request
        response = await call_next(request)

        # Add CORS headers if origin is allowed
        if origin and origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
            logger.info(f"✅ Added GET/POST CORS headers for origin: {origin}")
        else:
            logger.warning(f"⚠️ Origin not in allowed list or missing: {origin}, allowed: {self.allowed_origins[:3]}...")

        return response
