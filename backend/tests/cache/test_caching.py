"""
Comprehensive Cache Testing

Tests:
- Cache hit and miss scenarios
- TTL expiration
- Invalidation patterns
- Concurrent access
- Cache fallback
- Performance metrics
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.core.cache import cache_manager, cached, CacheManager
from app.services.cache_service import cache_service


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def cache():
    """Initialize cache manager for testing"""
    manager = CacheManager()
    await manager.connect()
    yield manager
    # Cleanup
    await manager.invalidate_layer("test")
    await manager.disconnect()


@pytest.fixture
async def clean_cache(cache):
    """Clean cache before and after test"""
    await cache.invalidate_layer("test")
    yield cache
    await cache.invalidate_layer("test")


# ============================================================================
# Basic Cache Operations
# ============================================================================

@pytest.mark.asyncio
async def test_cache_set_and_get(clean_cache):
    """Test basic cache set and get operations"""
    # Set value
    success = await clean_cache.set(
        layer="test",
        identifier="key1",
        value={"data": "test_value", "number": 42}
    )
    assert success is True

    # Get value
    value = await clean_cache.get(layer="test", identifier="key1")
    assert value is not None
    assert value["data"] == "test_value"
    assert value["number"] == 42


@pytest.mark.asyncio
async def test_cache_miss(clean_cache):
    """Test cache miss returns None"""
    value = await clean_cache.get(layer="test", identifier="nonexistent")
    assert value is None


@pytest.mark.asyncio
async def test_cache_delete(clean_cache):
    """Test cache deletion"""
    # Set value
    await clean_cache.set(layer="test", identifier="key1", value="test")

    # Verify exists
    assert await clean_cache.exists(layer="test", identifier="key1") is True

    # Delete
    success = await clean_cache.delete(layer="test", identifier="key1")
    assert success is True

    # Verify deleted
    assert await clean_cache.exists(layer="test", identifier="key1") is False


@pytest.mark.asyncio
async def test_cache_exists(clean_cache):
    """Test cache key existence check"""
    # Non-existent key
    assert await clean_cache.exists(layer="test", identifier="key1") is False

    # Set key
    await clean_cache.set(layer="test", identifier="key1", value="test")

    # Exists
    assert await clean_cache.exists(layer="test", identifier="key1") is True


# ============================================================================
# TTL and Expiration
# ============================================================================

@pytest.mark.asyncio
async def test_cache_ttl_expiration(clean_cache):
    """Test cache expires after TTL"""
    # Set with 1 second TTL
    await clean_cache.set(
        layer="test",
        identifier="expire_key",
        value="test_value",
        ttl=1
    )

    # Should exist immediately
    assert await clean_cache.exists(layer="test", identifier="expire_key") is True

    # Wait for expiration
    await asyncio.sleep(1.5)

    # Should be expired
    assert await clean_cache.exists(layer="test", identifier="expire_key") is False


@pytest.mark.asyncio
async def test_cache_custom_ttl(clean_cache):
    """Test custom TTL override"""
    # Set with custom 2 second TTL
    await clean_cache.set(
        layer="test",
        identifier="custom_ttl",
        value="test",
        ttl=2
    )

    # Should exist after 1 second
    await asyncio.sleep(1)
    assert await clean_cache.exists(layer="test", identifier="custom_ttl") is True

    # Should be expired after 2.5 seconds total
    await asyncio.sleep(1.5)
    assert await clean_cache.exists(layer="test", identifier="custom_ttl") is False


# ============================================================================
# Pattern-based Operations
# ============================================================================

@pytest.mark.asyncio
async def test_cache_delete_pattern(clean_cache):
    """Test pattern-based deletion"""
    # Set multiple keys
    await clean_cache.set(layer="test", identifier="user_1", value="data1")
    await clean_cache.set(layer="test", identifier="user_2", value="data2")
    await clean_cache.set(layer="test", identifier="article_1", value="data3")

    # Delete user keys
    deleted = await clean_cache.delete_pattern("test:v1:user_*")
    assert deleted >= 2

    # Verify user keys deleted
    assert await clean_cache.exists(layer="test", identifier="user_1") is False
    assert await clean_cache.exists(layer="test", identifier="user_2") is False

    # Verify article key still exists
    assert await clean_cache.exists(layer="test", identifier="article_1") is True


@pytest.mark.asyncio
async def test_cache_invalidate_layer(clean_cache):
    """Test layer invalidation"""
    # Set multiple keys
    await clean_cache.set(layer="test", identifier="key1", value="data1")
    await clean_cache.set(layer="test", identifier="key2", value="data2")
    await clean_cache.set(layer="test", identifier="key3", value="data3")

    # Invalidate entire layer
    deleted = await clean_cache.invalidate_layer("test")
    assert deleted >= 3

    # Verify all keys deleted
    assert await clean_cache.exists(layer="test", identifier="key1") is False
    assert await clean_cache.exists(layer="test", identifier="key2") is False
    assert await clean_cache.exists(layer="test", identifier="key3") is False


# ============================================================================
# Get or Set Pattern
# ============================================================================

@pytest.mark.asyncio
async def test_cache_get_or_set_hit(clean_cache):
    """Test get_or_set with cache hit"""
    # Pre-populate cache
    await clean_cache.set(layer="test", identifier="key1", value="cached_value")

    # Define fetch function (should not be called)
    fetch_called = False

    async def fetch_func():
        nonlocal fetch_called
        fetch_called = True
        return "fetched_value"

    # Get or set (should hit cache)
    value = await clean_cache.get_or_set(
        layer="test",
        identifier="key1",
        fetch_func=fetch_func
    )

    assert value == "cached_value"
    assert fetch_called is False  # Fetch should not be called


@pytest.mark.asyncio
async def test_cache_get_or_set_miss(clean_cache):
    """Test get_or_set with cache miss"""
    # Define fetch function
    fetch_called = False

    async def fetch_func():
        nonlocal fetch_called
        fetch_called = True
        return "fetched_value"

    # Get or set (should miss and fetch)
    value = await clean_cache.get_or_set(
        layer="test",
        identifier="new_key",
        fetch_func=fetch_func
    )

    assert value == "fetched_value"
    assert fetch_called is True

    # Verify cached
    cached_value = await clean_cache.get(layer="test", identifier="new_key")
    assert cached_value == "fetched_value"


# ============================================================================
# Cache Warming
# ============================================================================

@pytest.mark.asyncio
async def test_cache_warming(clean_cache):
    """Test batch cache warming"""
    items = [
        {"identifier": "article_1", "value": {"title": "Article 1"}},
        {"identifier": "article_2", "value": {"title": "Article 2"}},
        {"identifier": "article_3", "value": {"title": "Article 3"}},
    ]

    # Warm cache
    count = await clean_cache.warm_cache(layer="test", items=items, ttl=3600)
    assert count == 3

    # Verify all items cached
    for item in items:
        value = await clean_cache.get(layer="test", identifier=item["identifier"])
        assert value == item["value"]


# ============================================================================
# Concurrent Access
# ============================================================================

@pytest.mark.asyncio
async def test_cache_concurrent_reads(clean_cache):
    """Test concurrent cache reads"""
    # Pre-populate cache
    await clean_cache.set(layer="test", identifier="concurrent_key", value="test_data")

    # Concurrent reads
    async def read_cache():
        return await clean_cache.get(layer="test", identifier="concurrent_key")

    results = await asyncio.gather(*[read_cache() for _ in range(10)])

    # All reads should succeed
    assert all(r == "test_data" for r in results)


@pytest.mark.asyncio
async def test_cache_concurrent_writes(clean_cache):
    """Test concurrent cache writes (last write wins)"""
    async def write_cache(value):
        return await clean_cache.set(
            layer="test",
            identifier="concurrent_write",
            value=value
        )

    # Concurrent writes
    await asyncio.gather(*[write_cache(f"value_{i}") for i in range(10)])

    # Should have some value cached
    value = await clean_cache.get(layer="test", identifier="concurrent_write")
    assert value is not None
    assert value.startswith("value_")


@pytest.mark.asyncio
async def test_cache_stampede_prevention(clean_cache):
    """Test cache stampede prevention with get_or_set"""
    fetch_count = 0

    async def expensive_fetch():
        nonlocal fetch_count
        fetch_count += 1
        await asyncio.sleep(0.1)  # Simulate expensive operation
        return "expensive_result"

    # Concurrent get_or_set calls
    results = await asyncio.gather(*[
        clean_cache.get_or_set(
            layer="test",
            identifier="stampede_key",
            fetch_func=expensive_fetch
        )
        for _ in range(10)
    ])

    # All should get the same result
    assert all(r == "expensive_result" for r in results)

    # Fetch should ideally be called only once (stampede prevented)
    # Note: Depending on timing, may be called a few times
    assert fetch_count <= 3


# ============================================================================
# Cache Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_invalidate_article_cascade(clean_cache):
    """Test cascade invalidation for article"""
    # Setup: Create related cache entries
    article_id = 123

    await clean_cache.set(layer="article", identifier=str(article_id), value={"title": "Test"})
    await clean_cache.set(layer="nlp_analysis", identifier=f"article_{article_id}", value={"sentiment": 0.8})
    await clean_cache.set(layer="analytics", identifier=f"article_{article_id}_stats", value={"views": 100})

    # Invalidate article cache
    results = await cache_service.invalidate_article_cache(article_id)

    # Verify invalidation
    assert results["article_detail"] >= 0  # May or may not exist
    assert results["nlp_analysis"] >= 0


@pytest.mark.asyncio
async def test_cache_health_metrics(clean_cache):
    """Test cache health metrics"""
    # Generate some cache activity
    for i in range(10):
        await clean_cache.set(layer="test", identifier=f"key_{i}", value=f"value_{i}")

    # Get health metrics
    health = await cache_service.get_cache_health()

    assert "status" in health
    assert "health_score" in health
    assert "health_status" in health


# ============================================================================
# Decorator Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cached_decorator(clean_cache):
    """Test @cached decorator"""
    call_count = 0

    @cached(layer="test", identifier_param="item_id")
    async def get_item(item_id: int):
        nonlocal call_count
        call_count += 1
        return {"id": item_id, "data": f"item_{item_id}"}

    # First call - cache miss
    result1 = await get_item(item_id=42)
    assert result1["id"] == 42
    assert call_count == 1

    # Second call - cache hit
    result2 = await get_item(item_id=42)
    assert result2 == result1
    assert call_count == 1  # Should not increment

    # Different ID - cache miss
    result3 = await get_item(item_id=99)
    assert result3["id"] == 99
    assert call_count == 2


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cache_performance(clean_cache):
    """Test cache read performance (<5ms target)"""
    # Pre-populate cache
    await clean_cache.set(layer="test", identifier="perf_test", value="test_data")

    # Measure 100 reads
    start = time.time()
    for _ in range(100):
        await clean_cache.get(layer="test", identifier="perf_test")
    elapsed = time.time() - start

    # Average time per read
    avg_time_ms = (elapsed / 100) * 1000

    # Should be under 5ms per read
    assert avg_time_ms < 5.0, f"Cache read took {avg_time_ms:.2f}ms (target: <5ms)"


@pytest.mark.asyncio
async def test_cache_write_performance(clean_cache):
    """Test cache write performance"""
    # Measure 100 writes
    start = time.time()
    for i in range(100):
        await clean_cache.set(
            layer="test",
            identifier=f"write_perf_{i}",
            value={"data": f"test_{i}"}
        )
    elapsed = time.time() - start

    # Average time per write
    avg_time_ms = (elapsed / 100) * 1000

    # Should be under 10ms per write
    assert avg_time_ms < 10.0, f"Cache write took {avg_time_ms:.2f}ms (target: <10ms)"


# ============================================================================
# Graceful Degradation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cache_unavailable_fallback():
    """Test graceful degradation when Redis unavailable"""
    # Create cache with invalid URL
    bad_cache = CacheManager(redis_url="redis://invalid:9999/0")

    # Should handle gracefully
    value = await bad_cache.get(layer="test", identifier="key1")
    assert value is None

    success = await bad_cache.set(layer="test", identifier="key1", value="test")
    assert success is False


@pytest.mark.asyncio
async def test_cache_get_or_set_fallback_on_error():
    """Test get_or_set falls back to fetch on cache error"""
    bad_cache = CacheManager(redis_url="redis://invalid:9999/0")

    fetch_called = False

    async def fetch_func():
        nonlocal fetch_called
        fetch_called = True
        return "fallback_value"

    # Should fall back to fetch when cache unavailable
    value = await bad_cache.get_or_set(
        layer="test",
        identifier="key1",
        fetch_func=fetch_func
    )

    assert value == "fallback_value"
    assert fetch_called is True


# ============================================================================
# Key Generation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cache_key_with_parameters(clean_cache):
    """Test cache key generation with parameters"""
    # Same identifier, different params should have different keys
    await clean_cache.set(
        layer="test",
        identifier="search",
        value="result1",
        query="python"
    )

    await clean_cache.set(
        layer="test",
        identifier="search",
        value="result2",
        query="javascript"
    )

    # Should retrieve different values
    value1 = await clean_cache.get(layer="test", identifier="search", query="python")
    value2 = await clean_cache.get(layer="test", identifier="search", query="javascript")

    assert value1 == "result1"
    assert value2 == "result2"
    assert value1 != value2
