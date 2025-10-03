"""
Tests for Response Compression Middleware

Test Coverage:
- Brotli compression
- Gzip compression fallback
- Compression threshold enforcement
- MIME type filtering
- Compression headers
- Compression ratios
- Performance metrics
"""

import pytest
import brotli
import gzip
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from httpx import AsyncClient
from app.middleware.compression import CompressionMiddleware, COMPRESSIBLE_TYPES


@pytest.fixture
def app():
    """Create test FastAPI app with compression middleware"""
    app = FastAPI()

    # Add compression middleware
    app.add_middleware(
        CompressionMiddleware,
        min_size=500,
        brotli_level=4,
        gzip_level=6,
        enabled=True,
    )

    @app.get("/json")
    async def json_endpoint():
        """Large JSON response for compression testing"""
        return JSONResponse({
            "data": [{"id": i, "name": f"Item {i}", "description": "A" * 100} for i in range(50)]
        })

    @app.get("/text")
    async def text_endpoint():
        """Large text response for compression testing"""
        return PlainTextResponse("Lorem ipsum dolor sit amet. " * 100)

    @app.get("/small")
    async def small_endpoint():
        """Small response (below threshold)"""
        return JSONResponse({"message": "small"})

    @app.get("/image")
    async def image_endpoint():
        """Image response (should not compress)"""
        return JSONResponse(
            {"data": "binary_image_data"},
            headers={"content-type": "image/jpeg"}
        )

    @app.get("/stats")
    async def stats_endpoint():
        """Get compression statistics"""
        middleware = None
        for m in app.user_middleware:
            if isinstance(m.cls, type) and issubclass(m.cls, CompressionMiddleware):
                # Access the middleware instance through the app
                pass
        return JSONResponse({"stats": "placeholder"})

    return app


@pytest.mark.asyncio
async def test_brotli_compression(app):
    """Test Brotli compression for supported clients"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/json",
            headers={"accept-encoding": "br, gzip"}
        )

        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "br"
        assert "vary" in response.headers
        assert response.headers["vary"] == "Accept-Encoding"

        # Verify response can be decompressed
        decompressed = brotli.decompress(response.content)
        data = json.loads(decompressed)
        assert "data" in data
        assert len(data["data"]) == 50

        # Check compression ratio header
        assert "x-compression-ratio" in response.headers
        ratio = float(response.headers["x-compression-ratio"].replace("%", ""))
        assert ratio > 50  # Should compress at least 50%


@pytest.mark.asyncio
async def test_gzip_compression_fallback(app):
    """Test Gzip compression when Brotli not supported"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/json",
            headers={"accept-encoding": "gzip"}
        )

        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "gzip"

        # Verify response can be decompressed
        decompressed = gzip.decompress(response.content)
        data = json.loads(decompressed)
        assert "data" in data
        assert len(data["data"]) == 50


@pytest.mark.asyncio
async def test_no_compression_below_threshold(app):
    """Test that small responses are not compressed"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/small",
            headers={"accept-encoding": "br, gzip"}
        )

        assert response.status_code == 200
        assert "content-encoding" not in response.headers

        # Response should be uncompressed JSON
        data = response.json()
        assert data["message"] == "small"


@pytest.mark.asyncio
async def test_skip_image_compression(app):
    """Test that images are not compressed"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/image",
            headers={"accept-encoding": "br, gzip"}
        )

        assert response.status_code == 200
        assert "content-encoding" not in response.headers
        assert response.headers.get("content-type") == "image/jpeg"


@pytest.mark.asyncio
async def test_no_compression_without_accept_encoding(app):
    """Test that compression is skipped if client doesn't support it"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/json")

        assert response.status_code == 200
        assert "content-encoding" not in response.headers


@pytest.mark.asyncio
async def test_compression_headers(app):
    """Test that all required compression headers are present"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/text",
            headers={"accept-encoding": "br"}
        )

        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "br"
        assert response.headers.get("vary") == "Accept-Encoding"
        assert "content-length" in response.headers
        assert "x-compression-ratio" in response.headers
        assert "x-compression-time-ms" in response.headers


@pytest.mark.asyncio
async def test_compression_ratio_json(app):
    """Test compression ratio for JSON responses"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get uncompressed size
        response_uncompressed = await client.get("/json")
        uncompressed_size = len(response_uncompressed.content)

        # Get compressed size
        response_compressed = await client.get(
            "/json",
            headers={"accept-encoding": "br"}
        )
        compressed_size = len(response_compressed.content)

        # Calculate compression ratio
        ratio = (1 - compressed_size / uncompressed_size) * 100

        # JSON should compress well (>60%)
        assert ratio > 60, f"Compression ratio {ratio:.1f}% below target 60%"

        # Verify header matches calculation
        header_ratio = float(
            response_compressed.headers["x-compression-ratio"].replace("%", "")
        )
        assert abs(ratio - header_ratio) < 1  # Allow 1% difference


@pytest.mark.asyncio
async def test_compression_performance(app):
    """Test compression performance overhead"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/json",
            headers={"accept-encoding": "br"}
        )

        # Check compression time header
        compression_time = float(response.headers["x-compression-time-ms"])

        # Compression should be fast (<10ms for this size)
        assert compression_time < 10, f"Compression took {compression_time}ms (target: <10ms)"


@pytest.mark.asyncio
async def test_brotli_vs_gzip_ratio():
    """Test that Brotli achieves better compression than Gzip"""
    test_data = b'{"data": ' + b'{"key": "value", "text": "Lorem ipsum dolor sit amet"}, ' * 100 + b'}'

    # Compress with Brotli
    brotli_compressed = brotli.compress(test_data, quality=4)
    brotli_ratio = (1 - len(brotli_compressed) / len(test_data)) * 100

    # Compress with Gzip
    gzip_compressed = gzip.compress(test_data, compresslevel=6)
    gzip_ratio = (1 - len(gzip_compressed) / len(test_data)) * 100

    # Brotli should be at least 10% better
    improvement = brotli_ratio - gzip_ratio
    assert improvement > 10, f"Brotli only {improvement:.1f}% better than Gzip"


@pytest.mark.asyncio
async def test_mime_type_filtering():
    """Test that only compressible MIME types are compressed"""
    app = FastAPI()

    middleware = CompressionMiddleware(
        app=app,
        min_size=100,
        enabled=True,
    )

    # Test compressible types
    assert middleware._should_compress("application/json")
    assert middleware._should_compress("text/html")
    assert middleware._should_compress("text/plain")
    assert middleware._should_compress("application/javascript")

    # Test non-compressible types
    assert not middleware._should_compress("image/jpeg")
    assert not middleware._should_compress("image/png")
    assert not middleware._should_compress("video/mp4")
    assert not middleware._should_compress("application/zip")


def test_compression_levels():
    """Test different compression levels"""
    test_data = b'{"message": "test data"} ' * 1000

    # Test Brotli levels
    brotli_1 = brotli.compress(test_data, quality=1)
    brotli_4 = brotli.compress(test_data, quality=4)
    brotli_11 = brotli.compress(test_data, quality=11)

    # Higher levels should produce smaller output
    assert len(brotli_11) <= len(brotli_4) <= len(brotli_1)

    # Test Gzip levels
    gzip_1 = gzip.compress(test_data, compresslevel=1)
    gzip_6 = gzip.compress(test_data, compresslevel=6)
    gzip_9 = gzip.compress(test_data, compresslevel=9)

    # Higher levels should produce smaller output
    assert len(gzip_9) <= len(gzip_6) <= len(gzip_1)


@pytest.mark.asyncio
async def test_disabled_compression():
    """Test that compression can be disabled"""
    app = FastAPI()

    app.add_middleware(
        CompressionMiddleware,
        enabled=False,
    )

    @app.get("/test")
    async def test_endpoint():
        return JSONResponse({"data": "test" * 1000})

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/test",
            headers={"accept-encoding": "br, gzip"}
        )

        # Should not be compressed
        assert "content-encoding" not in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
