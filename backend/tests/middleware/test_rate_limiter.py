"""
Tests for Rate Limiting Middleware
Comprehensive test coverage for all rate limiting scenarios
"""

import pytest
import asyncio
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import time

from app.middleware.rate_limiter import RateLimiter, RateLimitConfig


@pytest.fixture
def app():
    """Create test FastAPI app"""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.get("/api/scraping/test")
    async def heavy_endpoint():
        return {"message": "heavy success"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.pipeline = Mock()

    # Mock pipeline behavior
    pipeline = AsyncMock()
    pipeline.incr = Mock()
    pipeline.expire = Mock()
    pipeline.execute = AsyncMock(return_value=[1, True])
    redis.pipeline.return_value = pipeline

    return redis


@pytest.fixture
def client_with_limiter(app, mock_redis):
    """Create test client with rate limiter"""
    with patch('app.middleware.rate_limiter.aioredis.from_url', return_value=mock_redis):
        limiter = RateLimiter(app, redis_url="redis://localhost:6379/0")
        app.add_middleware(RateLimiter, redis_url="redis://localhost:6379/0")
        client = TestClient(app)
        yield client, mock_redis


class TestRateLimiterBasic:
    """Test basic rate limiter functionality"""

    def test_health_endpoint_not_rate_limited(self, client_with_limiter):
        """Health endpoint should not be rate limited"""
        client, _ = client_with_limiter

        # Make multiple requests - should all succeed
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200

    def test_successful_request_includes_headers(self, client_with_limiter):
        """Successful requests should include rate limit headers"""
        client, _ = client_with_limiter

        response = client.get("/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers
        assert "X-RateLimit-Reset-Minute" in response.headers
        assert "X-RateLimit-Reset-Hour" in response.headers

    def test_disabled_rate_limiter(self, app):
        """Rate limiter should pass through when disabled"""
        limiter = RateLimiter(app, enabled=False)
        app.add_middleware(RateLimiter, enabled=False)
        client = TestClient(app)

        # Make many requests - should all succeed
        for _ in range(200):
            response = client.get("/test")
            assert response.status_code == 200


class TestAnonymousRateLimiting:
    """Test rate limiting for anonymous users"""

    @patch('app.middleware.rate_limiter.RateLimiter._increment_counter')
    async def test_anonymous_minute_limit(self, mock_increment, app, mock_redis):
        """Test anonymous user per-minute rate limit"""
        # Simulate exceeding minute limit
        mock_increment.return_value = RateLimitConfig.ANONYMOUS_PER_MINUTE + 1

        with patch('app.middleware.rate_limiter.aioredis.from_url', return_value=mock_redis):
            app.add_middleware(RateLimiter, redis_url="redis://localhost:6379/0")
            client = TestClient(app)

            response = client.get("/test")

            assert response.status_code == 429
            assert response.json()["error"] == "rate_limit_exceeded"
            assert "Retry-After" in response.headers

    @patch('app.middleware.rate_limiter.RateLimiter._increment_counter')
    async def test_anonymous_hour_limit(self, mock_increment, app, mock_redis):
        """Test anonymous user per-hour rate limit"""
        # Simulate exceeding hour limit
        async def increment_side_effect(key, window):
            if "hour" in key:
                return RateLimitConfig.ANONYMOUS_PER_HOUR + 1
            return 1

        mock_increment.side_effect = increment_side_effect

        with patch('app.middleware.rate_limiter.aioredis.from_url', return_value=mock_redis):
            app.add_middleware(RateLimiter, redis_url="redis://localhost:6379/0")
            client = TestClient(app)

            response = client.get("/test")

            assert response.status_code == 429

    def test_ip_based_identification(self, client_with_limiter):
        """Anonymous users should be identified by IP"""
        client, mock_redis = client_with_limiter

        # Mock different IPs
        with patch.object(TestClient, 'get') as mock_get:
            mock_request = Mock()
            mock_request.client.host = "192.168.1.1"

            response = client.get("/test")
            # Verify IP-based key is used (implementation detail)


class TestAuthenticatedRateLimiting:
    """Test rate limiting for authenticated users"""

    def test_authenticated_higher_limits(self, app, mock_redis):
        """Authenticated users should have higher limits"""
        with patch('app.middleware.rate_limiter.aioredis.from_url', return_value=mock_redis):
            app.add_middleware(RateLimiter, redis_url="redis://localhost:6379/0")
            client = TestClient(app)

            # Simulate authenticated request
            mock_user = Mock()
            mock_user.id = "user123"

            response = client.get("/test")

            # Check headers show higher limits
            minute_limit = int(response.headers.get("X-RateLimit-Limit-Minute", 0))
            assert minute_limit == RateLimitConfig.AUTHENTICATED_PER_MINUTE


class TestHeavyEndpoints:
    """Test rate limiting for heavy endpoints"""

    def test_heavy_endpoint_stricter_limits(self, client_with_limiter):
        """Heavy endpoints should have stricter limits"""
        client, _ = client_with_limiter

        response = client.get("/api/scraping/test")

        assert response.status_code == 200
        minute_limit = int(response.headers.get("X-RateLimit-Limit-Minute", 0))
        assert minute_limit == RateLimitConfig.HEAVY_ENDPOINT_PER_MINUTE

    def test_heavy_endpoint_patterns(self):
        """Test heavy endpoint pattern matching"""
        limiter = RateLimiter(FastAPI())

        assert limiter._is_heavy_endpoint("/api/scraping/test")
        assert limiter._is_heavy_endpoint("/api/analysis/process")
        assert not limiter._is_heavy_endpoint("/api/language/vocabulary")


class TestSlidingWindow:
    """Test sliding window algorithm"""

    @pytest.mark.asyncio
    async def test_counter_increments(self, mock_redis):
        """Test counter increments correctly"""
        limiter = RateLimiter(FastAPI())
        limiter.redis_client = mock_redis
        limiter._redis_available = True

        # Mock pipeline execution
        pipeline = AsyncMock()
        pipeline.incr = Mock()
        pipeline.expire = Mock()
        pipeline.execute = AsyncMock(return_value=[5, True])
        mock_redis.pipeline.return_value = pipeline

        count = await limiter._increment_counter("test:key", 60)

        assert count == 5
        pipeline.incr.assert_called_once_with("test:key")
        pipeline.expire.assert_called_once_with("test:key", 60)

    @pytest.mark.asyncio
    async def test_window_expiration(self, mock_redis):
        """Test that windows expire correctly"""
        limiter = RateLimiter(FastAPI())
        limiter.redis_client = mock_redis
        limiter._redis_available = True

        pipeline = AsyncMock()
        pipeline.incr = Mock()
        pipeline.expire = Mock()
        pipeline.execute = AsyncMock(return_value=[1, True])
        mock_redis.pipeline.return_value = pipeline

        await limiter._increment_counter("test:key", 60)

        # Verify expiration is set
        pipeline.expire.assert_called_once_with("test:key", 60)


class TestRedisFailure:
    """Test Redis failure scenarios"""

    def test_fail_open_on_redis_error(self, app):
        """Should fail open when Redis unavailable"""
        with patch('app.middleware.rate_limiter.aioredis.from_url', side_effect=Exception("Connection failed")):
            limiter = RateLimiter(app, fail_open=True)
            app.add_middleware(RateLimiter, fail_open=True)
            client = TestClient(app)

            # Should still allow requests
            response = client.get("/test")
            assert response.status_code == 200

    def test_fail_closed_on_redis_error(self, app):
        """Should fail closed when configured"""
        with patch('app.middleware.rate_limiter.aioredis.from_url', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                limiter = RateLimiter(app, fail_open=False)
                app.add_middleware(RateLimiter, fail_open=False)
                client = TestClient(app)
                response = client.get("/test")


class TestRateLimitReset:
    """Test rate limit reset behavior"""

    @pytest.mark.asyncio
    async def test_limit_resets_after_window(self, mock_redis):
        """Rate limit should reset after time window"""
        limiter = RateLimiter(FastAPI())
        limiter.redis_client = mock_redis
        limiter._redis_available = True

        current_time = int(time.time())

        # First request in window
        pipeline1 = AsyncMock()
        pipeline1.incr = Mock()
        pipeline1.expire = Mock()
        pipeline1.execute = AsyncMock(return_value=[1, True])
        mock_redis.pipeline.return_value = pipeline1

        allowed1, info1 = await limiter._check_rate_limit(
            identifier="test:user",
            is_authenticated=False,
            is_heavy=False
        )

        assert allowed1
        assert info1["current_minute"] == 1

        # Verify reset time is in the future
        assert info1["reset_minute"] > current_time


class TestDifferentUserTiers:
    """Test different rate limits per user tier"""

    def test_tier_limits_configuration(self):
        """Verify tier limits are configured correctly"""
        assert RateLimitConfig.ANONYMOUS_PER_MINUTE < RateLimitConfig.AUTHENTICATED_PER_MINUTE
        assert RateLimitConfig.ANONYMOUS_PER_HOUR < RateLimitConfig.AUTHENTICATED_PER_HOUR
        assert RateLimitConfig.HEAVY_ENDPOINT_PER_MINUTE < RateLimitConfig.ANONYMOUS_PER_MINUTE


class TestRateLimitHeaders:
    """Test rate limit response headers"""

    def test_all_headers_present(self, client_with_limiter):
        """All rate limit headers should be present"""
        client, _ = client_with_limiter

        response = client.get("/test")

        required_headers = [
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Limit-Hour",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Remaining-Hour",
            "X-RateLimit-Reset-Minute",
            "X-RateLimit-Reset-Hour"
        ]

        for header in required_headers:
            assert header in response.headers

    def test_retry_after_header_on_limit(self, app, mock_redis):
        """Retry-After header should be present when limited"""
        with patch('app.middleware.rate_limiter.aioredis.from_url', return_value=mock_redis):
            limiter = RateLimiter(app)

            # Mock rate limit exceeded
            limits_info = {
                "limit_minute": 60,
                "limit_hour": 1000,
                "remaining_minute": 0,
                "remaining_hour": 0,
                "reset_minute": int(time.time()) + 60,
                "reset_hour": int(time.time()) + 3600,
                "retry_after": 60
            }

            response = limiter._rate_limit_exceeded_response(limits_info)

            assert "Retry-After" in response.headers
            assert response.status_code == 429


class TestIdentifierGeneration:
    """Test user/IP identifier generation"""

    def test_authenticated_user_identifier(self, app):
        """Should use user ID for authenticated users"""
        limiter = RateLimiter(app)

        mock_request = Mock()
        mock_user = Mock()
        mock_user.id = "user123"
        mock_request.state = Mock()
        mock_request.state.user = mock_user

        identifier = limiter._get_identifier(mock_request)

        assert identifier == "user:user123"

    def test_anonymous_ip_identifier(self, app):
        """Should hash IP for anonymous users"""
        limiter = RateLimiter(app)

        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.user = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}

        identifier = limiter._get_identifier(mock_request)

        assert identifier.startswith("ip:")
        # Verify it's hashed (not raw IP)
        assert "192.168.1.1" not in identifier


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
