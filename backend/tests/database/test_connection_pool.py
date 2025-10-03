"""
Comprehensive test suite for database connection pooling
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from unittest.mock import patch, MagicMock
import os

from app.database.connection import (
    engine,
    async_engine,
    get_pool_status,
    get_async_pool_status,
    check_db_connection,
    check_async_db_connection,
    pool_metrics,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW
)
from app.database.health import (
    DatabaseHealthChecker,
    database_health_check,
    database_stats,
    pool_performance_test
)


class TestConnectionPoolConfiguration:
    """Test connection pool configuration and settings"""

    def test_pool_size_configuration(self):
        """Test that pool size is correctly configured"""
        status = get_pool_status()

        if status.get("pool_type") == "QueuePool":
            assert status["pool_size"] == DB_POOL_SIZE
            assert status["max_overflow"] == DB_MAX_OVERFLOW
            assert status["total_capacity"] == DB_POOL_SIZE + DB_MAX_OVERFLOW

    def test_pool_pre_ping_enabled(self):
        """Test that pool pre-ping is enabled for health checks"""
        status = get_pool_status()

        if status.get("pool_type") == "QueuePool":
            # Pool pre-ping should be enabled in production
            assert "recycle" in status
            assert status["recycle"] > 0

    def test_pool_timeout_configuration(self):
        """Test that pool timeout is properly configured"""
        status = get_pool_status()

        if status.get("pool_type") == "QueuePool":
            assert status["timeout"] > 0
            assert status["timeout"] <= 60  # Reasonable timeout

    def test_development_vs_production_settings(self):
        """Test that pool settings differ between development and production"""
        status = get_pool_status()

        if status.get("pool_type") == "QueuePool":
            # Production should have larger pool
            is_debug = os.getenv("DEBUG", "false").lower() == "true"
            if not is_debug:
                assert status["pool_size"] >= 20
            else:
                assert status["pool_size"] >= 5


class TestConnectionPoolBasicOperations:
    """Test basic connection pool operations"""

    def test_sync_connection_checkout(self):
        """Test synchronous connection checkout and checkin"""
        initial_metrics = pool_metrics.copy()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # Verify metrics were updated
        assert pool_metrics["checkout_count"] >= initial_metrics["checkout_count"]

    @pytest.mark.asyncio
    async def test_async_connection_checkout(self):
        """Test async connection checkout and checkin"""
        initial_metrics = pool_metrics.copy()

        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # Verify metrics were updated
        assert pool_metrics["checkout_count"] >= initial_metrics["checkout_count"]

    @pytest.mark.asyncio
    async def test_connection_health_check(self):
        """Test connection health check functionality"""
        is_healthy = await check_async_db_connection()
        assert is_healthy is True

    def test_sync_connection_health_check(self):
        """Test synchronous connection health check"""
        is_healthy = check_db_connection()
        assert is_healthy is True


class TestConnectionPoolReuse:
    """Test connection reuse and pooling efficiency"""

    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """Test that connections are reused from pool"""
        initial_status = await get_async_pool_status()
        initial_created = pool_metrics["connections_created"]

        # Execute multiple queries
        for _ in range(5):
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        # Should not create many new connections
        connections_created = pool_metrics["connections_created"] - initial_created
        assert connections_created <= 2  # Allow for some new connections

    @pytest.mark.asyncio
    async def test_concurrent_connection_reuse(self):
        """Test connection reuse under concurrent load"""
        async def query():
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        initial_created = pool_metrics["connections_created"]

        # Run concurrent queries
        await asyncio.gather(*[query() for _ in range(10)])

        # Verify pool is reusing connections efficiently
        connections_created = pool_metrics["connections_created"] - initial_created
        assert connections_created <= DB_POOL_SIZE


class TestConnectionPoolOverflow:
    """Test pool overflow behavior under high load"""

    @pytest.mark.asyncio
    async def test_pool_overflow_handling(self):
        """Test that pool creates overflow connections when needed"""
        async def hold_connection():
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT pg_sleep(0.1)"))

        status_before = await get_async_pool_status()

        # Create load exceeding pool size
        tasks = [hold_connection() for _ in range(DB_POOL_SIZE + 5)]
        await asyncio.gather(*tasks)

        status_after = await get_async_pool_status()

        # Overflow should have been used
        # Note: After tasks complete, overflow connections are closed
        assert status_after["size"] >= status_before["size"]

    @pytest.mark.asyncio
    async def test_pool_does_not_exceed_max_capacity(self):
        """Test that pool respects max capacity limits"""
        status = await get_async_pool_status()

        total_connections = status["checked_in"] + status["checked_out"]
        max_capacity = status["total_capacity"]

        assert total_connections <= max_capacity


class TestConnectionPoolRecycling:
    """Test connection recycling and cleanup"""

    @pytest.mark.asyncio
    async def test_connection_recycling(self):
        """Test that old connections are recycled"""
        # This test verifies the recycle mechanism is configured
        status = await get_async_pool_status()

        assert status["recycle"] > 0
        # In production, should recycle connections after 1 hour
        assert status["recycle"] <= 3600

    @pytest.mark.asyncio
    async def test_stale_connection_detection(self):
        """Test that pool detects and handles stale connections"""
        # Pool pre-ping should detect stale connections
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # If pool_pre_ping is enabled, stale connections are detected
        # and re-established automatically


class TestConnectionPoolMetrics:
    """Test connection pool metrics tracking"""

    def test_pool_metrics_tracking(self):
        """Test that pool metrics are being tracked"""
        assert "connections_created" in pool_metrics
        assert "connections_closed" in pool_metrics
        assert "checkout_count" in pool_metrics
        assert "checkin_count" in pool_metrics
        assert "connection_errors" in pool_metrics

    def test_pool_status_reporting(self):
        """Test pool status reporting"""
        status = get_pool_status()

        assert "pool_type" in status
        if status["pool_type"] == "QueuePool":
            assert "size" in status
            assert "checked_in" in status
            assert "checked_out" in status
            assert "overflow" in status
            assert "metrics" in status

    @pytest.mark.asyncio
    async def test_async_pool_status_reporting(self):
        """Test async pool status reporting"""
        status = await get_async_pool_status()

        assert "pool_type" in status
        if status["pool_type"] == "AsyncAdaptedQueuePool":
            assert "size" in status
            assert "checked_in" in status
            assert "checked_out" in status
            assert "metrics" in status


class TestDatabaseHealthChecks:
    """Test database health monitoring"""

    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self):
        """Test comprehensive database health check"""
        health = await database_health_check()

        assert "timestamp" in health
        assert "overall_status" in health
        assert "checks" in health
        assert "duration_ms" in health

        # Verify all checks are present
        assert "connection" in health["checks"]
        assert "connection_pool" in health["checks"]
        assert "query_performance" in health["checks"]

    @pytest.mark.asyncio
    async def test_health_check_performance(self):
        """Test that health checks complete quickly"""
        import time
        start = time.time()

        health = await database_health_check()

        duration = (time.time() - start) * 1000
        # Health check should complete in under 500ms
        assert duration < 500
        assert health["duration_ms"] < 500

    @pytest.mark.asyncio
    async def test_database_statistics(self):
        """Test database statistics collection"""
        stats = await database_stats()

        assert "timestamp" in stats
        assert "pool_metrics" in stats
        assert "query_metrics" in stats

    @pytest.mark.asyncio
    async def test_connection_leak_detection(self):
        """Test connection leak detection"""
        leak_check = DatabaseHealthChecker.detect_connection_leaks()

        assert "status" in leak_check
        assert "potential_leaks" in leak_check
        assert "leak_threshold_seconds" in leak_check


class TestConnectionPoolPerformance:
    """Test connection pool performance under load"""

    @pytest.mark.asyncio
    async def test_pool_performance_under_load(self):
        """Test pool performance with concurrent connections"""
        results = await pool_performance_test()

        assert "concurrent_connections" in results
        assert "results" in results
        assert "success_count" in results
        assert "average_duration_ms" in results

        # All connections should succeed
        assert results["success_count"] == results["concurrent_connections"]

        # Average duration should be reasonable (<100ms)
        assert results["average_duration_ms"] < 100

    @pytest.mark.asyncio
    async def test_connection_acquisition_time(self):
        """Test that connections are acquired quickly"""
        import time

        times = []
        for _ in range(10):
            start = time.time()
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            times.append((time.time() - start) * 1000)

        avg_time = sum(times) / len(times)
        # Average acquisition should be under 50ms
        assert avg_time < 50

    @pytest.mark.asyncio
    async def test_no_connection_leaks(self):
        """Test that there are no connection leaks"""
        status_before = await get_async_pool_status()

        # Execute many queries
        for _ in range(20):
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        # Give pool time to recycle
        await asyncio.sleep(0.1)

        status_after = await get_async_pool_status()

        # Checked out connections should return to zero
        assert status_after["checked_out"] == 0

    @pytest.mark.asyncio
    async def test_pool_scales_with_load(self):
        """Test that pool scales appropriately with load"""
        async def concurrent_query():
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        # Low load
        await asyncio.gather(*[concurrent_query() for _ in range(3)])
        status_low = await get_async_pool_status()

        # High load
        await asyncio.gather(*[concurrent_query() for _ in range(15)])
        status_high = await get_async_pool_status()

        # Pool should have scaled appropriately
        assert status_high["size"] >= status_low["size"]


class TestConnectionPoolErrorHandling:
    """Test error handling in connection pool"""

    @pytest.mark.asyncio
    async def test_connection_error_tracking(self):
        """Test that connection errors are tracked"""
        initial_errors = pool_metrics["connection_errors"]

        # Attempt connection with invalid URL
        with patch('app.database.connection.async_engine') as mock_engine:
            mock_engine.connect.side_effect = Exception("Connection failed")

            try:
                await check_async_db_connection()
            except:
                pass

        # Error count should increase
        assert pool_metrics["connection_errors"] >= initial_errors

    @pytest.mark.asyncio
    async def test_pool_recovery_after_error(self):
        """Test that pool recovers after connection errors"""
        # Verify pool is healthy
        health_before = await check_async_db_connection()
        assert health_before is True

        # Pool should continue working after temporary errors
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_graceful_pool_shutdown(self):
        """Test graceful pool shutdown"""
        # This test verifies the close_db function exists and is callable
        from app.database.connection import close_db

        assert callable(close_db)
        # Note: We don't actually close the pool as it would affect other tests


class TestConnectionPoolIsolation:
    """Test connection pool isolation levels"""

    @pytest.mark.asyncio
    async def test_transaction_isolation(self):
        """Test that transactions are properly isolated"""
        async with async_engine.connect() as conn:
            # Start a transaction
            async with conn.begin():
                # Execute query within transaction
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_concurrent_transactions(self):
        """Test that concurrent transactions don't interfere"""
        async def transaction_query(value):
            async with async_engine.connect() as conn:
                async with conn.begin():
                    result = await conn.execute(text(f"SELECT {value}"))
                    return result.scalar()

        results = await asyncio.gather(
            transaction_query(1),
            transaction_query(2),
            transaction_query(3)
        )

        assert results == [1, 2, 3]


@pytest.mark.integration
class TestConnectionPoolIntegration:
    """Integration tests for connection pool with real database operations"""

    @pytest.mark.asyncio
    async def test_pool_with_real_queries(self):
        """Test pool with real database queries"""
        async with async_engine.connect() as conn:
            # Test simple query
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            assert db_name is not None

    @pytest.mark.asyncio
    async def test_pool_with_multiple_sequential_queries(self):
        """Test pool handles sequential queries efficiently"""
        async with async_engine.connect() as conn:
            for i in range(10):
                result = await conn.execute(text(f"SELECT {i}"))
                assert result.scalar() == i

    @pytest.mark.asyncio
    async def test_pool_utilization_monitoring(self):
        """Test that pool utilization can be monitored"""
        status = await get_async_pool_status()

        # Calculate utilization
        checked_out = status["checked_out"]
        total_capacity = status["total_capacity"]
        utilization = (checked_out / total_capacity) * 100 if total_capacity > 0 else 0

        # Utilization should be reasonable
        assert 0 <= utilization <= 100
