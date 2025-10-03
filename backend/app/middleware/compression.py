"""
Response Compression Middleware
Implements Brotli and Gzip compression for API responses

Priority:
1. Brotli (br) - Best compression ratio, modern browsers
2. Gzip (gzip) - Universal fallback support

Features:
- Content-based compression selection
- Minimum size threshold (500 bytes)
- MIME type filtering
- Compression level configuration
- Performance metrics tracking
"""

import brotli
import gzip
import io
import time
from typing import Set, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.datastructures import Headers, MutableHeaders
import logging

logger = logging.getLogger(__name__)


# MIME types that should be compressed
COMPRESSIBLE_TYPES: Set[str] = {
    "text/html",
    "text/css",
    "text/plain",
    "text/xml",
    "text/javascript",
    "application/json",
    "application/javascript",
    "application/xml",
    "application/xhtml+xml",
    "application/rss+xml",
    "application/atom+xml",
    "application/ld+json",
    "application/vnd.api+json",
    "image/svg+xml",
}

# MIME types that are already compressed (skip compression)
SKIP_COMPRESSION_TYPES: Set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/avif",
    "video/mp4",
    "video/webm",
    "video/ogg",
    "audio/mpeg",
    "audio/ogg",
    "audio/webm",
    "application/zip",
    "application/gzip",
    "application/x-gzip",
    "application/x-brotli",
    "application/octet-stream",
}


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for compressing HTTP responses

    Configuration:
    - min_size: Minimum response size in bytes to trigger compression
    - compression_level: Compression level (1-11 for brotli, 1-9 for gzip)
    - enabled: Enable/disable compression globally
    """

    def __init__(
        self,
        app,
        min_size: int = 500,
        brotli_level: int = 4,
        gzip_level: int = 6,
        enabled: bool = True,
    ):
        """
        Initialize compression middleware

        Args:
            app: ASGI application
            min_size: Minimum response size in bytes (default: 500)
            brotli_level: Brotli compression level 1-11 (default: 4, balanced)
            gzip_level: Gzip compression level 1-9 (default: 6, balanced)
            enabled: Enable/disable compression (default: True)
        """
        super().__init__(app)
        self.min_size = min_size
        self.brotli_level = brotli_level
        self.gzip_level = gzip_level
        self.enabled = enabled

        # Compression statistics
        self.stats = {
            "total_requests": 0,
            "compressed_responses": 0,
            "brotli_count": 0,
            "gzip_count": 0,
            "bytes_saved": 0,
            "compression_time_ms": 0,
        }

    async def dispatch(self, request: Request, call_next):
        """Process request and compress response if applicable"""
        if not self.enabled:
            return await call_next(request)

        self.stats["total_requests"] += 1

        # Get client's accepted encodings
        accept_encoding = request.headers.get("accept-encoding", "").lower()

        # Determine compression method (priority: brotli > gzip)
        compression_method = None
        if "br" in accept_encoding:
            compression_method = "br"
        elif "gzip" in accept_encoding:
            compression_method = "gzip"

        # Get response
        response = await call_next(request)

        # Skip compression if no method supported or already compressed
        if not compression_method or self._is_already_compressed(response):
            return response

        # Get response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Check if response is large enough to compress
        if len(response_body) < self.min_size:
            return self._create_response(response, response_body)

        # Check if content type is compressible
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if not self._should_compress(content_type):
            return self._create_response(response, response_body)

        # Compress response
        start_time = time.time()
        compressed_body = self._compress(response_body, compression_method)
        compression_time = (time.time() - start_time) * 1000  # ms

        # Update statistics
        bytes_saved = len(response_body) - len(compressed_body)
        self.stats["compressed_responses"] += 1
        self.stats["bytes_saved"] += bytes_saved
        self.stats["compression_time_ms"] += compression_time

        if compression_method == "br":
            self.stats["brotli_count"] += 1
        elif compression_method == "gzip":
            self.stats["gzip_count"] += 1

        # Log compression details
        compression_ratio = (1 - len(compressed_body) / len(response_body)) * 100
        logger.debug(
            f"Compressed response: {compression_method} | "
            f"Original: {len(response_body)} bytes | "
            f"Compressed: {len(compressed_body)} bytes | "
            f"Saved: {bytes_saved} bytes ({compression_ratio:.1f}%) | "
            f"Time: {compression_time:.2f}ms"
        )

        # Create compressed response
        headers = MutableHeaders(response.headers)
        headers["content-encoding"] = compression_method
        headers["content-length"] = str(len(compressed_body))
        headers["vary"] = "Accept-Encoding"

        # Add compression performance header in development
        headers["x-compression-ratio"] = f"{compression_ratio:.1f}%"
        headers["x-compression-time-ms"] = f"{compression_time:.2f}"

        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=dict(headers),
            media_type=content_type,
        )

    def _compress(self, data: bytes, method: str) -> bytes:
        """Compress data using specified method"""
        if method == "br":
            return brotli.compress(
                data,
                mode=brotli.MODE_TEXT,
                quality=self.brotli_level,
            )
        elif method == "gzip":
            buffer = io.BytesIO()
            with gzip.GzipFile(
                fileobj=buffer,
                mode="wb",
                compresslevel=self.gzip_level,
            ) as gz:
                gz.write(data)
            return buffer.getvalue()
        else:
            return data

    def _should_compress(self, content_type: str) -> bool:
        """Check if content type should be compressed"""
        # Skip if already compressed format
        if content_type in SKIP_COMPRESSION_TYPES:
            return False

        # Compress if in compressible list
        if content_type in COMPRESSIBLE_TYPES:
            return True

        # Check for wildcard matches
        for compressible in COMPRESSIBLE_TYPES:
            if content_type.startswith(compressible.split("/")[0]):
                return True

        return False

    def _is_already_compressed(self, response: Response) -> bool:
        """Check if response is already compressed"""
        encoding = response.headers.get("content-encoding", "").lower()
        return encoding in {"gzip", "br", "deflate", "compress"}

    def _create_response(self, original: Response, body: bytes) -> Response:
        """Create response from original with body"""
        return Response(
            content=body,
            status_code=original.status_code,
            headers=dict(original.headers),
        )

    def get_stats(self) -> dict:
        """Get compression statistics"""
        total = self.stats["total_requests"]
        compressed = self.stats["compressed_responses"]

        return {
            "enabled": self.enabled,
            "total_requests": total,
            "compressed_responses": compressed,
            "compression_rate": f"{(compressed / total * 100):.1f}%" if total > 0 else "0%",
            "brotli_count": self.stats["brotli_count"],
            "gzip_count": self.stats["gzip_count"],
            "total_bytes_saved": self.stats["bytes_saved"],
            "average_compression_time_ms": (
                self.stats["compression_time_ms"] / compressed
                if compressed > 0
                else 0
            ),
            "min_size_threshold": self.min_size,
            "brotli_level": self.brotli_level,
            "gzip_level": self.gzip_level,
        }
