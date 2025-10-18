"""
Comprehensive Health Check Tests

Tests for all health check endpoints and dependency validation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import tempfile
import os

from app.api.health import (
    check_database_health,
    check_redis_health,
    check_elasticsearch_health,
    check_filesystem_health,
    calculate_overall_health,
    HealthStatus,
    basic_health_check,
    readiness_check,
    liveness_check,
    comprehensive_health_check,
    startup_check
)


class TestDatabaseHealthCheck:
    """Test database health check functionality"""

    @pytest.mark.asyncio
    async def test_database_health_success(self):
        """Test successful database health check"""
        mock_health = {
            "overall_status": "healthy",
            "checks": {
                "connection": {"status": "healthy", "message": "Connected"},
                "connection_pool": {"status": "healthy", "details": {"checked_out": 2}},
                "query_performance": {"query_time_ms": 25.5}
            },
            "duration_ms": 50.0
        }

        with patch('app.api.health.DatabaseHealthChecker.comprehensive_health_check',
                   new_callable=AsyncMock, return_value=mock_health):
            result = await check_database_health()

            assert result["status"] == HealthStatus.HEALTHY
            assert result["response_time_ms"] == 50.0
            assert result["details"]["query_performance_ms"] == 25.5

    @pytest.mark.asyncio
    async def test_database_health_timeout(self):
        """Test database health check timeout"""
        async def slow_check():
            await asyncio.sleep(10)
            return {}

        with patch('app.api.health.DatabaseHealthChecker.comprehensive_health_check',
                   side_effect=slow_check):
            result = await check_database_health(timeout=0.1)

            assert result["status"] == HealthStatus.TIMEOUT
            assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_database_health_failure(self):
        """Test database health check failure"""
        with patch('app.api.health.DatabaseHealthChecker.comprehensive_health_check',
                   side_effect=Exception("Connection refused")):
            result = await check_database_health()

            assert result["status"] == HealthStatus.UNHEALTHY
            assert "Connection refused" in result["error"]


class TestRedisHealthCheck:
    """Test Redis health check functionality"""

    @pytest.mark.asyncio
    async def test_redis_health_success(self):
        """Test successful Redis health check"""
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(return_value=True)

        mock_stats = {
            "status": "available",
            "connected": True,
            "total_keys": 1250,
            "memory_used_mb": 45.2,
            "hit_rate_percent": 82.5
        }

        with patch('app.api.health.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache._redis = mock_redis
            mock_cache.get_stats = AsyncMock(return_value=mock_stats)

            result = await check_redis_health()

            assert result["status"] == HealthStatus.HEALTHY
            assert result["details"]["hit_rate_percent"] == 82.5
            assert result["details"]["total_keys"] == 1250

    @pytest.mark.asyncio
    async def test_redis_health_unavailable(self):
        """Test Redis health when not connected"""
        with patch('app.api.health.cache_manager') as mock_cache:
            mock_cache.is_available = False

            result = await check_redis_health()

            assert result["status"] == HealthStatus.UNAVAILABLE
            assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_redis_health_degraded_hit_rate(self):
        """Test Redis health with low hit rate"""
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(return_value=True)

        mock_stats = {
            "status": "available",
            "total_keys": 500,
            "hit_rate_percent": 35.0  # Below 50%
        }

        with patch('app.api.health.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache._redis = mock_redis
            mock_cache.get_stats = AsyncMock(return_value=mock_stats)

            result = await check_redis_health()

            assert result["status"] == HealthStatus.DEGRADED
            assert "hit rate below 50%" in result["warning"].lower()

    @pytest.mark.asyncio
    async def test_redis_health_timeout(self):
        """Test Redis health check timeout"""
        mock_redis = MagicMock()

        async def slow_ping():
            await asyncio.sleep(10)
            return True

        mock_redis.ping = slow_ping

        with patch('app.api.health.cache_manager') as mock_cache:
            mock_cache.is_available = True
            mock_cache._redis = mock_redis

            result = await check_redis_health(timeout=0.1)

            assert result["status"] == HealthStatus.TIMEOUT
            assert "timeout" in result["error"].lower()


class TestElasticsearchHealthCheck:
    """Test Elasticsearch health check functionality"""

    @pytest.mark.asyncio
    async def test_elasticsearch_health_success(self):
        """Test successful Elasticsearch health check"""
        mock_es_client = MagicMock()
        mock_health = {
            "healthy": True,
            "status": "green",
            "number_of_nodes": 3,
            "active_shards": 15
        }
        mock_es_client.health_check = AsyncMock(return_value=mock_health)

        with patch('app.api.health.settings') as mock_settings:
            mock_settings.ELASTICSEARCH_ENABLED = True
            with patch('app.api.health.get_elasticsearch_client',
                       return_value=mock_es_client):
                result = await check_elasticsearch_health()

                assert result["status"] == HealthStatus.HEALTHY
                assert result["details"]["cluster_status"] == "green"
                assert result["details"]["number_of_nodes"] == 3

    @pytest.mark.asyncio
    async def test_elasticsearch_health_yellow(self):
        """Test Elasticsearch with yellow status"""
        mock_es_client = MagicMock()
        mock_health = {
            "healthy": True,
            "status": "yellow",
            "number_of_nodes": 1
        }
        mock_es_client.health_check = AsyncMock(return_value=mock_health)

        with patch('app.api.health.settings') as mock_settings:
            mock_settings.ELASTICSEARCH_ENABLED = True
            with patch('app.api.health.get_elasticsearch_client',
                       return_value=mock_es_client):
                result = await check_elasticsearch_health()

                assert result["status"] == HealthStatus.DEGRADED
                assert result["details"]["cluster_status"] == "yellow"

    @pytest.mark.asyncio
    async def test_elasticsearch_not_configured(self):
        """Test Elasticsearch when not configured"""
        with patch('app.api.health.settings') as mock_settings:
            mock_settings.ELASTICSEARCH_ENABLED = False

            result = await check_elasticsearch_health()

            assert result["status"] == HealthStatus.DEGRADED
            assert "not configured" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_elasticsearch_timeout(self):
        """Test Elasticsearch health check timeout"""
        async def slow_health():
            await asyncio.sleep(10)
            return {}

        mock_es_client = MagicMock()
        mock_es_client.health_check = slow_health

        with patch('app.api.health.settings') as mock_settings:
            mock_settings.ELASTICSEARCH_ENABLED = True
            with patch('app.api.health.get_elasticsearch_client',
                       return_value=mock_es_client):
                result = await check_elasticsearch_health(timeout=0.1)

                assert result["status"] == HealthStatus.TIMEOUT


class TestFilesystemHealthCheck:
    """Test filesystem health check functionality"""

    @pytest.mark.asyncio
    async def test_filesystem_health_success(self):
        """Test successful filesystem health check"""
        result = await check_filesystem_health()

        assert result["status"] in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert result["details"]["writable"] is True
        assert result["details"]["readable"] is True
        assert "free_space_gb" in result["details"]

    @pytest.mark.asyncio
    async def test_filesystem_health_read_write(self):
        """Test filesystem read/write operations"""
        result = await check_filesystem_health()

        # Should successfully read and write
        assert result["details"]["writable"] is True
        assert result["details"]["readable"] is True
        assert result["status"] != HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_filesystem_health_low_space_warning(self):
        """Test filesystem warning on low space"""
        with patch('os.statvfs') as mock_statvfs:
            # Mock low disk space (0.5 GB free)
            mock_stat = MagicMock()
            mock_stat.f_bavail = 131072  # blocks
            mock_stat.f_frsize = 4096    # block size
            # Total: 131072 * 4096 = 536870912 bytes ≈ 0.5 GB
            mock_statvfs.return_value = mock_stat

            result = await check_filesystem_health()

            # Should be degraded due to low space
            assert result["status"] == HealthStatus.DEGRADED
            assert "low disk space" in result["warning"].lower()


class TestOverallHealthCalculation:
    """Test overall health status calculation"""

    @pytest.mark.asyncio
    async def test_all_healthy(self):
        """Test overall status when all components healthy"""
        checks = {
            "database": {"status": HealthStatus.HEALTHY},
            "redis": {"status": HealthStatus.HEALTHY},
            "elasticsearch": {"status": HealthStatus.HEALTHY},
            "filesystem": {"status": HealthStatus.HEALTHY}
        }

        status = await calculate_overall_health(checks)
        assert status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_critical_component_unhealthy(self):
        """Test overall status when critical component is unhealthy"""
        checks = {
            "database": {"status": HealthStatus.UNHEALTHY},
            "redis": {"status": HealthStatus.HEALTHY},
            "elasticsearch": {"status": HealthStatus.HEALTHY},
            "filesystem": {"status": HealthStatus.HEALTHY}
        }

        status = await calculate_overall_health(checks)
        assert status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_non_critical_degraded(self):
        """Test overall status when non-critical component degraded"""
        checks = {
            "database": {"status": HealthStatus.HEALTHY},
            "redis": {"status": HealthStatus.HEALTHY},
            "elasticsearch": {"status": HealthStatus.DEGRADED},
            "filesystem": {"status": HealthStatus.HEALTHY}
        }

        status = await calculate_overall_health(checks)
        assert status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_timeout_as_unhealthy(self):
        """Test that timeout on critical component is treated as unhealthy"""
        checks = {
            "database": {"status": HealthStatus.TIMEOUT},
            "redis": {"status": HealthStatus.HEALTHY},
            "elasticsearch": {"status": HealthStatus.HEALTHY},
            "filesystem": {"status": HealthStatus.HEALTHY}
        }

        status = await calculate_overall_health(checks)
        assert status == HealthStatus.UNHEALTHY


class TestHealthEndpoints:
    """Test health check API endpoints"""

    @pytest.mark.asyncio
    async def test_basic_health_check(self):
        """Test basic health check endpoint"""
        result = await basic_health_check()

        assert result["status"] == "ok"
        assert result["service"] == "openlearn"

    @pytest.mark.asyncio
    async def test_liveness_check(self):
        """Test Kubernetes liveness probe"""
        result = await liveness_check()

        assert result["alive"] is True
        assert result["status"] == "healthy"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_readiness_check_ready(self):
        """Test readiness check when service is ready"""
        mock_db_health = {
            "status": HealthStatus.HEALTHY,
            "details": {},
            "response_time_ms": 25
        }
        mock_redis_health = {
            "status": HealthStatus.HEALTHY,
            "details": {},
            "response_time_ms": 10
        }

        with patch('app.api.health.check_database_health',
                   return_value=mock_db_health):
            with patch('app.api.health.check_redis_health',
                       return_value=mock_redis_health):
                result = await readiness_check()

                assert result["ready"] is True
                assert result["status"] in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    @pytest.mark.asyncio
    async def test_readiness_check_not_ready(self):
        """Test readiness check when service is not ready"""
        mock_db_health = {
            "status": HealthStatus.UNHEALTHY,
            "error": "Connection failed"
        }

        with patch('app.api.health.check_database_health',
                   return_value=mock_db_health):
            with patch('app.api.health.check_redis_health',
                       return_value={"status": HealthStatus.HEALTHY}):
                result = await readiness_check()

                assert result["ready"] is False

    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self):
        """Test comprehensive health check endpoint"""
        mock_db = {"status": HealthStatus.HEALTHY, "response_time_ms": 30}
        mock_redis = {"status": HealthStatus.HEALTHY, "response_time_ms": 15}
        mock_es = {"status": HealthStatus.DEGRADED, "response_time_ms": 50}
        mock_fs = {"status": HealthStatus.HEALTHY, "response_time_ms": 5}

        with patch('app.api.health.check_database_health', return_value=mock_db):
            with patch('app.api.health.check_redis_health', return_value=mock_redis):
                with patch('app.api.health.check_elasticsearch_health', return_value=mock_es):
                    with patch('app.api.health.check_filesystem_health', return_value=mock_fs):
                        result = await comprehensive_health_check()

                        assert "status" in result
                        assert "health_score" in result
                        assert "checks" in result
                        assert "database" in result["checks"]
                        assert "redis" in result["checks"]
                        assert "elasticsearch" in result["checks"]
                        assert "filesystem" in result["checks"]
                        assert result["health_score"] >= 0
                        assert result["health_score"] <= 100

    @pytest.mark.asyncio
    async def test_startup_check(self):
        """Test Kubernetes startup probe"""
        mock_db = {"status": HealthStatus.HEALTHY}
        mock_redis = {"status": HealthStatus.HEALTHY}

        with patch('app.api.health.check_database_health', return_value=mock_db):
            with patch('app.api.health.check_redis_health', return_value=mock_redis):
                result = await startup_check()

                assert result["started"] is True
                assert "checks" in result
                assert "timestamp" in result


class TestHealthCheckPerformance:
    """Test health check performance and timeouts"""

    @pytest.mark.asyncio
    async def test_health_check_response_time(self):
        """Test that health checks complete within acceptable time"""
        import time

        start = time.time()
        await basic_health_check()
        duration = time.time() - start

        # Basic health check should be very fast (<10ms)
        assert duration < 0.01

    @pytest.mark.asyncio
    async def test_comprehensive_check_parallel_execution(self):
        """Test that comprehensive check runs checks in parallel"""
        import time

        # Mock checks with 100ms delay each
        async def slow_check():
            await asyncio.sleep(0.1)
            return {"status": HealthStatus.HEALTHY}

        with patch('app.api.health.check_database_health', side_effect=slow_check):
            with patch('app.api.health.check_redis_health', side_effect=slow_check):
                with patch('app.api.health.check_elasticsearch_health', side_effect=slow_check):
                    with patch('app.api.health.check_filesystem_health', side_effect=slow_check):
                        start = time.time()
                        await comprehensive_health_check()
                        duration = time.time() - start

                        # Should complete in ~100ms (parallel), not ~400ms (sequential)
                        assert duration < 0.2


class TestHealthCheckIntegration:
    """Integration tests for health checks"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_database_connection_real(self):
        """Test real database connection health check"""
        # This would require actual database connection
        # Skip in unit tests, run in integration environment
        pytest.skip("Integration test - requires real database")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_redis_connection_real(self):
        """Test real Redis connection health check"""
        # This would require actual Redis connection
        # Skip in unit tests, run in integration environment
        pytest.skip("Integration test - requires real Redis")
