"""
Comprehensive Cache Middleware Tests

Tests for:
- HTTP response caching with ETags
- Cache-Control headers
- Conditional requests (304 Not Modified)
- Cache invalidation
- Per-endpoint cache configuration
- Cache bypass for authenticated requests
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import hashlib

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.middleware.cache_middleware import (
    CacheMiddleware,
    invalidate_http_cache,
    invalidate_endpoint_cache,
)


class TestCacheMiddleware:
    """Test cache middleware functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = FastAPI()

        # Mock cache manager
        self.mock_cache_manager = Mock()
        self.mock_cache_manager.is_available = True

    @pytest.fixture
    def cache_middleware(self):
        """Create cache middleware instance"""
        return CacheMiddleware(self.app, enabled=True)

    @pytest.mark.asyncio
    async def test_cache_miss_stores_response(self, cache_middleware):
        """Cache miss should store response for future requests"""
        # Mock cache manager
        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache.get = AsyncMock(return_value=None)  # Cache miss
            mock_cache.set = AsyncMock()

            # Create mock request
            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/api/scraping/sources"
            request.url.scheme = "http"
            request.headers = {"accept": "application/json"}
            request.query_params = {}

            # Create mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}

            body_content = b'{"data": "test"}'

            async def body_iter():
                yield body_content

            mock_response.body_iterator = body_iter()

            # Mock call_next
            async def call_next(req):
                return mock_response

            # Execute middleware
            response = await cache_middleware.dispatch(request, call_next)

            # Verify cache.set was called
            assert mock_cache.set.called
            call_args = mock_cache.set.call_args
            assert call_args[1]['layer'] == 'http_response'
            assert 'etag' in call_args[1]['value']
            assert call_args[1]['value']['status_code'] == 200

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_response(self, cache_middleware):
        """Cache hit should return cached response"""
        cached_body = '{"cached": "data"}'
        cached_etag = '"abc123"'

        cached_data = {
            'body': cached_body,
            'status_code': 200,
            'content_type': 'application/json',
            'etag': cached_etag,
            'cached_at': datetime.utcnow().isoformat()
        }

        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache.get = AsyncMock(return_value=cached_data)

            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/api/scraping/sources"
            request.headers = {}
            request.query_params = {}

            async def call_next(req):
                pytest.fail("Should not call next middleware on cache hit")

            response = await cache_middleware.dispatch(request, call_next)

            assert response.status_code == 200
            assert response.headers['ETag'] == cached_etag
            assert response.headers['X-Cache'] == 'HIT'
            assert 'Cache-Control' in response.headers

    @pytest.mark.asyncio
    async def test_conditional_request_304_not_modified(self, cache_middleware):
        """Conditional request with matching ETag should return 304"""
        cached_etag = '"matching_etag"'

        cached_data = {
            'body': '{"data": "test"}',
            'status_code': 200,
            'content_type': 'application/json',
            'etag': cached_etag,
            'cached_at': datetime.utcnow().isoformat()
        }

        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache.get = AsyncMock(return_value=cached_data)

            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/api/scraping/sources"
            request.headers = {"if-none-match": cached_etag}
            request.query_params = {}

            async def call_next(req):
                pytest.fail("Should not call next middleware on 304")

            response = await cache_middleware.dispatch(request, call_next)

            assert response.status_code == 304
            assert response.headers['ETag'] == cached_etag

    @pytest.mark.asyncio
    async def test_cache_bypass_for_post_requests(self, cache_middleware):
        """POST requests should bypass cache"""
        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True

            request = Mock(spec=Request)
            request.method = "POST"
            request.url.path = "/api/scraping/sources"

            mock_response = Mock()
            mock_response.status_code = 201

            async def call_next(req):
                return mock_response

            response = await cache_middleware.dispatch(request, call_next)

            # Cache should not be checked or set for POST
            assert not mock_cache.get.called
            assert not mock_cache.set.called
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_cache_bypass_for_authenticated_requests(self, cache_middleware):
        """Authenticated requests should bypass cache"""
        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True

            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/api/scraping/sources"
            request.headers = {"authorization": "Bearer token123"}

            mock_response = Mock()
            mock_response.status_code = 200

            async def call_next(req):
                return mock_response

            response = await cache_middleware.dispatch(request, call_next)

            # Cache should be bypassed for authenticated requests
            assert not mock_cache.get.called
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cache_disabled(self, cache_middleware):
        """Cache middleware should be skipped when disabled"""
        # Create middleware with caching disabled
        disabled_middleware = CacheMiddleware(self.app, enabled=False)

        request = Mock(spec=Request)
        request.method = "GET"

        mock_response = Mock()
        mock_response.status_code = 200

        async def call_next(req):
            return mock_response

        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            response = await disabled_middleware.dispatch(request, call_next)

            # Cache manager should not be used when disabled
            assert not mock_cache.get.called
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cache_unavailable(self, cache_middleware):
        """Cache middleware should skip when cache is unavailable"""
        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = False

            request = Mock(spec=Request)
            request.method = "GET"

            mock_response = Mock()
            mock_response.status_code = 200

            async def call_next(req):
                return mock_response

            response = await cache_middleware.dispatch(request, call_next)

            assert not mock_cache.get.called
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_non_200_response_not_cached(self, cache_middleware):
        """Non-200 responses should not be cached"""
        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache.get = AsyncMock(return_value=None)

            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/api/scraping/sources"
            request.headers = {}
            request.query_params = {}

            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.headers = {}

            async def call_next(req):
                return mock_response

            response = await cache_middleware.dispatch(request, call_next)

            # Cache should not be set for non-200 responses
            assert not mock_cache.set.called
            assert response.status_code == 404

    def test_generate_cache_key_includes_query_params(self, cache_middleware):
        """Cache key should include query parameters"""
        request1 = Mock(spec=Request)
        request1.url.path = "/api/scraping/content"
        request1.query_params = {"page": "1", "limit": "10"}
        request1.headers = {}

        request2 = Mock(spec=Request)
        request2.url.path = "/api/scraping/content"
        request2.query_params = {"page": "2", "limit": "10"}
        request2.headers = {}

        key1 = cache_middleware._generate_cache_key(request1)
        key2 = cache_middleware._generate_cache_key(request2)

        assert key1 != key2  # Different query params = different keys

    def test_generate_cache_key_same_for_identical_requests(self, cache_middleware):
        """Cache key should be identical for identical requests"""
        request1 = Mock(spec=Request)
        request1.url.path = "/api/scraping/content"
        request1.query_params = {"page": "1"}
        request1.headers = {"accept": "application/json"}

        request2 = Mock(spec=Request)
        request2.url.path = "/api/scraping/content"
        request2.query_params = {"page": "1"}
        request2.headers = {"accept": "application/json"}

        key1 = cache_middleware._generate_cache_key(request1)
        key2 = cache_middleware._generate_cache_key(request2)

        assert key1 == key2

    def test_generate_etag_consistency(self, cache_middleware):
        """ETag generation should be consistent for same content"""
        body = b'{"data": "test content"}'

        etag1 = cache_middleware._generate_etag(body)
        etag2 = cache_middleware._generate_etag(body)

        assert etag1 == etag2

    def test_generate_etag_different_for_different_content(self, cache_middleware):
        """ETag should be different for different content"""
        body1 = b'{"data": "content1"}'
        body2 = b'{"data": "content2"}'

        etag1 = cache_middleware._generate_etag(body1)
        etag2 = cache_middleware._generate_etag(body2)

        assert etag1 != etag2

    def test_is_cacheable_endpoint(self, cache_middleware):
        """Check if endpoint is cacheable"""
        # Cacheable endpoints
        cacheable_requests = [
            ("/api/scraping/sources", "GET"),
            ("/api/scraping/content", "GET"),
            ("/api/analysis/results", "GET"),
            ("/health", "GET"),
        ]

        for path, method in cacheable_requests:
            request = Mock(spec=Request)
            request.url.path = path
            request.method = method

            assert cache_middleware._is_cacheable_endpoint(request) is True

        # Non-cacheable endpoints
        non_cacheable_requests = [
            ("/api/auth/login", "POST"),
            ("/api/scraping/sources", "POST"),
            ("/api/admin/settings", "GET"),
        ]

        for path, method in non_cacheable_requests:
            request = Mock(spec=Request)
            request.url.path = path
            request.method = method

            if method == "GET":
                # GET to non-whitelisted endpoint
                assert cache_middleware._is_cacheable_endpoint(request) is False

    def test_get_cache_config_returns_correct_duration(self, cache_middleware):
        """Cache config should return correct TTL for endpoints"""
        request = Mock(spec=Request)
        request.url.path = "/api/scraping/sources"
        request.method = "GET"

        config = cache_middleware._get_cache_config(request)

        assert config is not None
        assert 'duration' in config
        assert config['duration'] == 7200  # 2 hours for sources

    @pytest.mark.asyncio
    async def test_invalidate_http_cache(self):
        """Test cache invalidation by pattern"""
        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.delete_pattern = AsyncMock(return_value=5)

            count = await invalidate_http_cache("http_response:*")

            assert count == 5
            mock_cache.delete_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_endpoint_cache(self):
        """Test endpoint-specific cache invalidation"""
        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.invalidate_layer = AsyncMock(return_value=3)

            count = await invalidate_endpoint_cache("/api/scraping/content")

            assert count == 3
            mock_cache.invalidate_layer.assert_called_once_with("http_response")


class TestCacheEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_cache_large_response(self):
        """Large responses should be cached correctly"""
        middleware = CacheMiddleware(FastAPI(), enabled=True)
        large_body = b'{"data": "' + b'x' * 100000 + b'"}'  # 100KB

        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/api/scraping/sources"
            request.headers = {}
            request.query_params = {}

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}

            async def body_iter():
                yield large_body

            mock_response.body_iterator = body_iter()

            async def call_next(req):
                return mock_response

            await middleware.dispatch(request, call_next)

            assert mock_cache.set.called
            cached_value = mock_cache.set.call_args[1]['value']
            assert len(cached_value['body']) > 100000

    @pytest.mark.asyncio
    async def test_cache_binary_response(self):
        """Binary responses should be handled"""
        middleware = CacheMiddleware(FastAPI(), enabled=True)

        # Binary content (e.g., image)
        binary_body = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'

        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/health"
            request.headers = {}
            request.query_params = {}

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "image/png"}

            async def body_iter():
                yield binary_body

            mock_response.body_iterator = body_iter()

            async def call_next(req):
                return mock_response

            # Should handle without errors
            await middleware.dispatch(request, call_next)

    @pytest.mark.asyncio
    async def test_cache_concurrent_requests(self):
        """Concurrent requests should handle cache correctly"""
        import asyncio

        middleware = CacheMiddleware(FastAPI(), enabled=True)

        with patch('app.middleware.cache_middleware.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            async def make_request():
                request = Mock(spec=Request)
                request.method = "GET"
                request.url.path = "/api/scraping/sources"
                request.headers = {}
                request.query_params = {}

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {"content-type": "application/json"}

                async def body_iter():
                    yield b'{"data": "test"}'

                mock_response.body_iterator = body_iter()

                async def call_next(req):
                    await asyncio.sleep(0.01)  # Simulate work
                    return mock_response

                return await middleware.dispatch(request, call_next)

            # Make 5 concurrent requests
            responses = await asyncio.gather(*[make_request() for _ in range(5)])

            assert len(responses) == 5
            # Cache should be set multiple times (no lock in current implementation)
            assert mock_cache.set.call_count >= 1
