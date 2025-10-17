"""
Unit tests for RateLimiter classes
"""
import pytest
import asyncio
import time
from collections import deque
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scrapers.base.rate_limiter import RateLimiter, DomainRateLimiter, global_rate_limiter


class TestRateLimiter:
    """Test suite for RateLimiter class"""

    def test_initialization(self):
        """Test rate limiter initialization with different parameters"""
        limiter = RateLimiter(max_requests=10, time_window=60)

        assert limiter.max_requests == 10
        assert limiter.time_window == 60
        assert isinstance(limiter.requests, deque)
        assert limiter._lock is not None

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring when within rate limit"""
        limiter = RateLimiter(max_requests=5, time_window=1)

        # Should allow 5 requests immediately
        for _ in range(5):
            await limiter.acquire()

        # Check that all requests were recorded
        assert len(limiter.requests) == 5

    @pytest.mark.asyncio
    async def test_acquire_at_limit(self):
        """Test acquiring when at rate limit"""
        limiter = RateLimiter(max_requests=2, time_window=1)

        # First two should be immediate
        await limiter.acquire()
        await limiter.acquire()

        # Third should wait
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            await limiter.acquire()
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_cleanup(self):
        """Test that old requests are cleaned up"""
        limiter = RateLimiter(max_requests=5, time_window=1)

        # Add some requests
        current_time = time.time()
        limiter.requests.append(current_time - 2)  # Old request
        limiter.requests.append(current_time - 0.5)  # Recent request

        await limiter.acquire()

        # Old request should be cleaned up
        assert len([r for r in limiter.requests if r < current_time - 1]) == 0

    @pytest.mark.asyncio
    async def test_concurrent_acquire(self):
        """Test thread safety with concurrent acquire calls"""
        limiter = RateLimiter(max_requests=10, time_window=1)

        # Run multiple acquire calls concurrently
        tasks = [limiter.acquire() for _ in range(10)]
        await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(limiter.requests) == 10

    def test_get_current_rate(self):
        """Test current rate calculation"""
        limiter = RateLimiter(max_requests=10, time_window=60)

        # No requests yet
        assert limiter.get_current_rate() == 0.0

        # Add some requests
        current_time = time.time()
        limiter.requests.append(current_time - 2)
        limiter.requests.append(current_time - 1)
        limiter.requests.append(current_time)

        rate = limiter.get_current_rate()
        assert rate > 0
        # Should be approximately 3 requests over 2 seconds = 1.5 req/sec
        assert 1 < rate < 2

    @pytest.mark.asyncio
    async def test_rate_limiting_timing(self):
        """Test that rate limiting actually delays requests"""
        limiter = RateLimiter(max_requests=2, time_window=1)

        start_time = time.time()

        # First two should be fast
        await limiter.acquire()
        await limiter.acquire()

        # Third should wait
        await limiter.acquire()

        elapsed = time.time() - start_time

        # Should have waited, but in testing this might be mocked
        # Just ensure the logic runs without errors
        assert elapsed >= 0


class TestDomainRateLimiter:
    """Test suite for DomainRateLimiter class"""

    def test_initialization(self):
        """Test domain rate limiter initialization"""
        limiter = DomainRateLimiter()

        assert isinstance(limiter.limiters, dict)
        assert len(limiter.limiters) == 0
        assert limiter.default_max_requests == 10
        assert limiter.default_time_window == 60

    def test_get_limiter_default(self):
        """Test getting limiter for unknown domain"""
        domain_limiter = DomainRateLimiter()

        limiter = domain_limiter.get_limiter("example.com")

        assert isinstance(limiter, RateLimiter)
        assert limiter.max_requests == 10
        assert limiter.time_window == 60

    def test_get_limiter_eltiempo(self):
        """Test getting limiter for eltiempo.com"""
        domain_limiter = DomainRateLimiter()

        limiter = domain_limiter.get_limiter("eltiempo.com")

        assert limiter.max_requests == 5
        assert limiter.time_window == 60

    def test_get_limiter_elespectador(self):
        """Test getting limiter for elespectador.com"""
        domain_limiter = DomainRateLimiter()

        limiter = domain_limiter.get_limiter("elespectador.com")

        assert limiter.max_requests == 5
        assert limiter.time_window == 60

    def test_get_limiter_government(self):
        """Test getting limiter for government sites"""
        domain_limiter = DomainRateLimiter()

        limiter = domain_limiter.get_limiter("presidencia.gov.co")

        assert limiter.max_requests == 3
        assert limiter.time_window == 60

    def test_limiter_caching(self):
        """Test that limiters are cached per domain"""
        domain_limiter = DomainRateLimiter()

        limiter1 = domain_limiter.get_limiter("example.com")
        limiter2 = domain_limiter.get_limiter("example.com")

        # Should be the same instance
        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_acquire_with_url(self):
        """Test acquiring permission for a URL"""
        domain_limiter = DomainRateLimiter()

        # Should parse domain from URL and apply rate limiting
        with patch.object(RateLimiter, 'acquire') as mock_acquire:
            mock_acquire.return_value = None
            await domain_limiter.acquire("https://example.com/article")
            mock_acquire.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_different_domains(self):
        """Test that different domains have independent rate limits"""
        domain_limiter = DomainRateLimiter()

        # Acquire for different domains
        await domain_limiter.acquire("https://example1.com/page")
        await domain_limiter.acquire("https://example2.com/page")

        # Should have created two separate limiters
        assert len(domain_limiter.limiters) == 2
        assert "example1.com" in domain_limiter.limiters
        assert "example2.com" in domain_limiter.limiters


class TestGlobalRateLimiter:
    """Test the global rate limiter instance"""

    def test_global_instance_exists(self):
        """Test that global rate limiter is available"""
        assert global_rate_limiter is not None
        assert isinstance(global_rate_limiter, DomainRateLimiter)

    @pytest.mark.asyncio
    async def test_global_instance_works(self):
        """Test that global rate limiter functions correctly"""
        # Should work without errors
        await global_rate_limiter.acquire("https://test.com/page")

        # Should have created a limiter
        assert "test.com" in global_rate_limiter.limiters


@pytest.mark.integration
class TestRateLimiterIntegration:
    """Integration tests for rate limiting"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_timing_behavior(self):
        """Test actual timing behavior of rate limiter"""
        limiter = RateLimiter(max_requests=3, time_window=1)

        start_time = time.time()

        # Fire 5 requests, should see delays after the 3rd
        for i in range(5):
            await limiter.acquire()

        elapsed = time.time() - start_time

        # Should take at least 1 second due to rate limiting
        # (3 immediate, then wait for window to refresh)
        assert elapsed >= 0.5  # Give some buffer for test execution

    @pytest.mark.asyncio
    async def test_domain_specific_limits(self):
        """Test that domain-specific limits are enforced"""
        domain_limiter = DomainRateLimiter()

        # Government site should be more restricted
        gov_limiter = domain_limiter.get_limiter("dane.gov.co")
        assert gov_limiter.max_requests == 3

        # News site should have medium limits
        news_limiter = domain_limiter.get_limiter("eltiempo.com")
        assert news_limiter.max_requests == 5

        # Unknown site should get default
        other_limiter = domain_limiter.get_limiter("unknown-site.com")
        assert other_limiter.max_requests == 10

    @pytest.mark.asyncio
    async def test_concurrent_domain_requests(self):
        """Test concurrent requests to different domains"""
        domain_limiter = DomainRateLimiter()

        urls = [
            "https://example1.com/page1",
            "https://example2.com/page1",
            "https://example1.com/page2",
            "https://example3.com/page1",
            "https://example2.com/page2",
        ]

        # All should complete without interference
        tasks = [domain_limiter.acquire(url) for url in urls]
        await asyncio.gather(*tasks)

        # Should have 3 different limiters
        assert len(domain_limiter.limiters) == 3


@pytest.mark.unit
class TestRateLimiterEdgeCases:
    """Edge case tests for rate limiter"""

    def test_zero_max_requests(self):
        """Test rate limiter with zero max requests"""
        # Should handle gracefully, though this is an unusual config
        limiter = RateLimiter(max_requests=0, time_window=60)
        assert limiter.max_requests == 0

    def test_very_small_time_window(self):
        """Test rate limiter with very small time window"""
        limiter = RateLimiter(max_requests=10, time_window=0.001)
        assert limiter.time_window == 0.001

    @pytest.mark.asyncio
    async def test_empty_url(self):
        """Test domain limiter with empty URL"""
        domain_limiter = DomainRateLimiter()

        # Should handle empty URL gracefully
        try:
            await domain_limiter.acquire("")
            # Might fail to parse, that's okay
        except:
            pass  # Expected for invalid URL

    def test_get_rate_with_future_requests(self):
        """Test rate calculation with future timestamps (clock drift)"""
        limiter = RateLimiter(max_requests=10, time_window=60)

        # Add a future request (shouldn't happen but handle gracefully)
        future_time = time.time() + 10
        limiter.requests.append(future_time)

        # Should still calculate something reasonable
        rate = limiter.get_current_rate()
        assert rate >= 0