"""
Simple unit tests for RateLimiter
"""
import pytest
import asyncio
import time
from scrapers.base.rate_limiter import RateLimiter


@pytest.mark.unit
def test_rate_limiter_initialization():
    """Test RateLimiter can be created"""
    limiter = RateLimiter(max_requests=10, time_window=60)
    assert limiter.max_requests == 10
    assert limiter.time_window == 60
    assert len(limiter.requests) == 0


@pytest.mark.unit
def test_rate_limiter_default_values():
    """Test RateLimiter uses default values"""
    limiter = RateLimiter()
    assert limiter.max_requests == 10
    assert limiter.time_window == 60


@pytest.mark.unit
def test_rate_limiter_get_current_rate_empty():
    """Test current rate when no requests"""
    limiter = RateLimiter(max_requests=5, time_window=60)
    rate = limiter.get_current_rate()
    assert rate == 0.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_acquire_single():
    """Test acquiring permission for single request"""
    limiter = RateLimiter(max_requests=10, time_window=60)
    await limiter.acquire()
    assert len(limiter.requests) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_acquire_multiple():
    """Test acquiring permission for multiple requests"""
    limiter = RateLimiter(max_requests=5, time_window=60)
    for _ in range(3):
        await limiter.acquire()
    assert len(limiter.requests) == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_tracks_timestamps():
    """Test that rate limiter tracks request timestamps"""
    limiter = RateLimiter(max_requests=10, time_window=60)
    before = time.time()
    await limiter.acquire()
    after = time.time()
    assert len(limiter.requests) == 1
    assert before <= limiter.requests[0] <= after
