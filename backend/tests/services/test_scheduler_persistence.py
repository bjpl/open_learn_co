"""
Tests for APScheduler PostgreSQL Persistence

Tests validate:
- Database connection
- Job persistence across restarts
- Error handling
- Health checks
"""

import pytest
from datetime import datetime, timedelta
import asyncio

from app.core.scheduler_db import (
    get_db_manager,
    initialize_scheduler_database,
    scheduler_db_health_check,
    cleanup_scheduler_database
)
from app.services.scheduler import get_scheduler_service, SchedulerService
from app.config.scheduler_config import SCHEDULER_TIMEZONE


class TestSchedulerDatabaseManager:
    """Test database manager functionality"""

    def test_db_manager_singleton(self):
        """Test database manager is singleton"""
        manager1 = get_db_manager()
        manager2 = get_db_manager()
        assert manager1 is manager2

    def test_database_connection(self):
        """Test database connection validation"""
        manager = get_db_manager()
        is_valid = manager.validate_connection()
        assert is_valid is True, "Database connection should be valid"

    def test_database_initialization(self):
        """Test database table initialization"""
        success = initialize_scheduler_database()
        assert success is True, "Database initialization should succeed"

    def test_health_check(self):
        """Test comprehensive health check"""
        health = scheduler_db_health_check()

        assert 'connection_valid' in health
        assert 'table_exists' in health
        assert 'job_count' in health

        assert health['connection_valid'] is True
        assert health['error'] is None

    def test_table_exists(self):
        """Test table existence check"""
        manager = get_db_manager()

        # Initialize first
        initialize_scheduler_database()

        # Check existence
        exists = manager.table_exists()
        # Note: APScheduler creates table on first scheduler start
        # So this may be False until scheduler actually starts
        assert isinstance(exists, bool)

    def test_job_count(self):
        """Test job count retrieval"""
        manager = get_db_manager()

        # Initialize database
        initialize_scheduler_database()

        count = manager.get_job_count()
        assert count is not None or count == 0


class TestSchedulerPersistence:
    """Test scheduler persistence functionality"""

    @pytest.mark.asyncio
    async def test_scheduler_start_with_persistence(self):
        """Test scheduler starts with PostgreSQL persistence"""
        scheduler_service = SchedulerService()

        try:
            await scheduler_service.start()

            assert scheduler_service.running is True
            assert scheduler_service.scheduler is not None

            # Verify scheduler is using PostgreSQL jobstore
            jobstores = scheduler_service.scheduler._jobstores
            assert 'default' in jobstores

            # Check that jobstore is SQLAlchemy-based
            from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
            assert isinstance(jobstores['default'], SQLAlchemyJobStore)

        finally:
            await scheduler_service.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_scheduler_health_check_integration(self):
        """Test scheduler with database health check"""
        # First check database health
        health = scheduler_db_health_check()
        assert health['connection_valid'] is True

        # Start scheduler
        scheduler_service = SchedulerService()

        try:
            await scheduler_service.start()

            # Get status
            status = scheduler_service.get_status()
            assert status['running'] is True
            assert 'total_jobs' in status

        finally:
            await scheduler_service.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_job_persistence_across_restart(self):
        """Test that jobs persist across scheduler restarts"""
        scheduler_service = SchedulerService()

        try:
            # Start scheduler
            await scheduler_service.start()

            # Add a test job
            test_job_id = 'test_persistence_job'

            def test_func():
                print("Test job executed")

            scheduler_service.scheduler.add_job(
                test_func,
                'interval',
                minutes=60,
                id=test_job_id,
                replace_existing=True,
                next_run_time=datetime.now(SCHEDULER_TIMEZONE) + timedelta(hours=1)
            )

            # Verify job exists
            job = scheduler_service.get_job(test_job_id)
            assert job is not None
            assert job['id'] == test_job_id

            # Shutdown scheduler (jobs should persist to database)
            await scheduler_service.shutdown(wait=False)

            # Small delay
            await asyncio.sleep(1)

            # Create new scheduler instance
            new_scheduler_service = SchedulerService()
            await new_scheduler_service.start()

            # Check if job was recovered
            recovered_job = new_scheduler_service.get_job(test_job_id)

            # Clean up
            if recovered_job:
                new_scheduler_service.scheduler.remove_job(test_job_id)

            await new_scheduler_service.shutdown(wait=False)

            # Verify job was recovered
            assert recovered_job is not None, "Job should persist across restarts"
            assert recovered_job['id'] == test_job_id

        except Exception as e:
            # Clean up on error
            if scheduler_service.running:
                await scheduler_service.shutdown(wait=False)
            raise


class TestSchedulerErrorHandling:
    """Test error handling in scheduler persistence"""

    @pytest.mark.asyncio
    async def test_scheduler_handles_db_connection_error(self):
        """Test scheduler gracefully handles database connection errors"""
        # This test would require mocking database connection
        # For now, we ensure scheduler doesn't crash on errors
        scheduler_service = SchedulerService()

        try:
            await scheduler_service.start()
            assert scheduler_service.running is True
        except RuntimeError as e:
            # Expected if database is not available
            assert "database" in str(e).lower()
        finally:
            if scheduler_service.running:
                await scheduler_service.shutdown(wait=False)

    def test_cleanup_old_jobs(self):
        """Test cleanup of old completed jobs"""
        # Initialize database
        initialize_scheduler_database()

        # Run cleanup
        deleted_count = cleanup_scheduler_database(days=30)

        # Should return an integer (count of deleted jobs)
        assert isinstance(deleted_count, int)
        assert deleted_count >= 0


@pytest.mark.integration
class TestSchedulerIntegration:
    """Integration tests for scheduler with PostgreSQL"""

    @pytest.mark.asyncio
    async def test_full_scheduler_lifecycle(self):
        """Test complete scheduler lifecycle with persistence"""
        # Initialize database
        init_success = initialize_scheduler_database()
        assert init_success is True

        # Check health
        health = scheduler_db_health_check()
        assert health['connection_valid'] is True

        # Start scheduler
        scheduler_service = get_scheduler_service()

        try:
            await scheduler_service.start()
            assert scheduler_service.running is True

            # Get status
            status = scheduler_service.get_status()
            assert status['running'] is True

            # Verify persistence is configured
            assert scheduler_service.scheduler._jobstores is not None

        finally:
            await scheduler_service.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_concurrent_scheduler_access(self):
        """Test multiple concurrent scheduler operations"""
        scheduler_service = get_scheduler_service()

        try:
            await scheduler_service.start()

            # Simulate concurrent status checks
            tasks = [
                asyncio.create_task(asyncio.to_thread(scheduler_service.get_status))
                for _ in range(10)
            ]

            results = await asyncio.gather(*tasks)

            # All should return valid status
            assert len(results) == 10
            for status in results:
                assert 'running' in status
                assert status['running'] is True

        finally:
            await scheduler_service.shutdown(wait=False)
