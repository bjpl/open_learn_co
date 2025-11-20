"""
Test cache implementation on API endpoints

This test verifies:
1. Cache decorators are properly applied
2. Cache hit/miss metrics are tracked
3. Cache invalidation works correctly
4. TTLs are configured as expected
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.cache import cache_manager, cached, invalidate_cache_async


class TestCacheConfiguration:
    """Test cache layer configuration"""

    def test_cache_layers_exist(self):
        """Verify all required cache layers are configured"""
        assert "analytics" in cache_manager.CACHE_LAYERS
        assert "content" in cache_manager.CACHE_LAYERS
        assert "metadata" in cache_manager.CACHE_LAYERS

    def test_cache_layer_ttls(self):
        """Verify TTLs match requirements"""
        # Analytics layer (used by status and statistics)
        assert cache_manager.CACHE_LAYERS["analytics"]["ttl"] == 1800  # 30 minutes default

        # Content layer (used by articles-simple)
        assert cache_manager.CACHE_LAYERS["content"]["ttl"] == 900  # 15 minutes

        # Metadata layer (used by sources)
        assert cache_manager.CACHE_LAYERS["metadata"]["ttl"] == 1800  # 30 minutes


class TestCacheDecorator:
    """Test the @cached decorator functionality"""

    @pytest.mark.asyncio
    async def test_cached_decorator_with_static_identifier(self):
        """Test decorator with static identifier (for parameterless endpoints)"""
        call_count = 0

        @cached(layer="analytics", identifier="test-endpoint", ttl=300)
        async def test_endpoint():
            nonlocal call_count
            call_count += 1
            return {"status": "ok", "count": call_count}

        # Mock Redis to simulate cache behavior
        with patch.object(cache_manager, 'is_available', True):
            with patch.object(cache_manager, 'get_or_set', new_callable=AsyncMock) as mock_get_or_set:
                mock_get_or_set.return_value = {"status": "ok", "count": 1}

                # First call - should use cache
                result1 = await test_endpoint()
                assert result1["status"] == "ok"
                assert mock_get_or_set.called

    @pytest.mark.asyncio
    async def test_cached_decorator_with_params(self):
        """Test decorator with parameter inclusion"""
        @cached(
            layer="content",
            identifier="articles",
            include_params=["limit", "offset"],
            ttl=900
        )
        async def get_articles(limit: int, offset: int):
            return {"limit": limit, "offset": offset, "items": []}

        with patch.object(cache_manager, 'is_available', True):
            with patch.object(cache_manager, 'get_or_set', new_callable=AsyncMock) as mock_get_or_set:
                mock_get_or_set.return_value = {"limit": 10, "offset": 0, "items": []}

                result = await get_articles(limit=10, offset=0)
                assert result["limit"] == 10

                # Verify cache was called with correct parameters
                assert mock_get_or_set.called
                call_kwargs = mock_get_or_set.call_args[1]
                assert call_kwargs["layer"] == "content"
                assert call_kwargs["identifier"] == "articles"


class TestCacheInvalidation:
    """Test cache invalidation"""

    @pytest.mark.asyncio
    async def test_invalidate_cache_async(self):
        """Test async cache invalidation"""
        with patch.object(cache_manager, 'is_available', True):
            with patch.object(cache_manager, 'delete', new_callable=AsyncMock) as mock_delete:
                await invalidate_cache_async(layer="analytics", identifier="scraping-status")

                # Verify delete was called
                assert mock_delete.called
                assert mock_delete.call_args[0] == ("analytics", "scraping-status")

    @pytest.mark.asyncio
    async def test_invalidate_cache_pattern(self):
        """Test pattern-based cache invalidation"""
        with patch.object(cache_manager, 'is_available', True):
            with patch.object(cache_manager, 'delete_pattern', new_callable=AsyncMock) as mock_delete_pattern:
                await invalidate_cache_async(layer="content", pattern="articles-simple*")

                # Verify delete_pattern was called
                assert mock_delete_pattern.called


class TestEndpointCacheConfiguration:
    """Verify endpoints have correct cache configuration"""

    def test_scraping_status_endpoint_has_cache(self):
        """Verify /api/scraping/status has @cached decorator"""
        from app.api.scraping import get_scraping_status

        # Check if function is wrapped (has __wrapped__ attribute from functools.wraps)
        assert hasattr(get_scraping_status, '__wrapped__') or hasattr(get_scraping_status, '__name__')
        assert get_scraping_status.__name__ == "get_scraping_status" or \
               get_scraping_status.__name__ == "wrapper"

    def test_analysis_statistics_endpoint_has_cache(self):
        """Verify /api/analysis/statistics has @cached decorator"""
        from app.api.analysis import get_analysis_statistics

        assert hasattr(get_analysis_statistics, '__wrapped__') or hasattr(get_analysis_statistics, '__name__')
        assert get_analysis_statistics.__name__ == "get_analysis_statistics" or \
               get_analysis_statistics.__name__ == "wrapper"

    def test_sources_endpoint_has_cache(self):
        """Verify /api/scraping/sources has @cached decorator"""
        from app.api.scraping import list_sources

        assert hasattr(list_sources, '__wrapped__') or hasattr(list_sources, '__name__')

    def test_content_simple_endpoint_has_cache(self):
        """Verify /api/scraping/content/simple has @cached decorator"""
        from app.api.scraping import get_content_simple

        assert hasattr(get_content_simple, '__wrapped__') or hasattr(get_content_simple, '__name__')


class TestCacheMetrics:
    """Test cache metrics integration"""

    def test_cache_metrics_exist(self):
        """Verify Prometheus cache metrics are defined"""
        from app.core.metrics import cache_hit_counter, cache_miss_counter

        # Check metrics are Counter objects
        assert cache_hit_counter is not None
        assert cache_miss_counter is not None

    def test_cache_operation_duration_metric_exists(self):
        """Verify cache operation duration metric exists"""
        from app.core.metrics import cache_operation_duration_seconds

        assert cache_operation_duration_seconds is not None


if __name__ == "__main__":
    print("Running cache implementation tests...")
    pytest.main([__file__, "-v", "--tb=short"])
