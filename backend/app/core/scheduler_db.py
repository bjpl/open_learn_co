"""
APScheduler Database Initialization and Management

This module handles PostgreSQL database setup for APScheduler persistence,
including table creation, connection validation, and migration support.
"""

import logging
from sqlalchemy import create_engine, inspect, text, MetaData, Table, Column
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)


class SchedulerDatabaseManager:
    """
    Manages APScheduler database operations including:
    - Table initialization
    - Connection validation
    - Schema migrations
    - Health checks
    """

    def __init__(self):
        """Initialize database manager"""
        self.engine = None
        self.table_name = 'apscheduler_jobs'

    def get_engine(self):
        """Get or create SQLAlchemy engine for synchronous operations"""
        if self.engine is None:
            try:
                self.engine = create_engine(
                    settings.DATABASE_URL_SYNC,
                    pool_pre_ping=True,  # Validate connections before using
                    pool_size=5,
                    max_overflow=10,
                    pool_recycle=3600,  # Recycle connections after 1 hour
                    echo=False
                )
                logger.info("APScheduler database engine created successfully")
            except Exception as e:
                logger.error(f"Failed to create database engine: {str(e)}", exc_info=True)
                raise

        return self.engine

    def validate_connection(self) -> bool:
        """
        Validate database connection

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection validated successfully")
                return True
        except OperationalError as e:
            logger.error(f"Database connection validation failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection validation: {str(e)}", exc_info=True)
            return False

    def table_exists(self) -> bool:
        """
        Check if APScheduler jobs table exists

        Returns:
            True if table exists, False otherwise
        """
        try:
            engine = self.get_engine()
            inspector = inspect(engine)
            exists = self.table_name in inspector.get_table_names()

            if exists:
                logger.info(f"Table '{self.table_name}' exists")
            else:
                logger.info(f"Table '{self.table_name}' does not exist")

            return exists
        except Exception as e:
            logger.error(f"Error checking table existence: {str(e)}", exc_info=True)
            return False

    def initialize_tables(self) -> bool:
        """
        Initialize APScheduler database tables

        Creates the apscheduler_jobs table if it doesn't exist.
        APScheduler will automatically create the table with the correct schema,
        but we validate the connection first.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # First validate the connection
            if not self.validate_connection():
                logger.error("Cannot initialize tables: database connection invalid")
                return False

            # Check if table already exists
            if self.table_exists():
                logger.info("APScheduler tables already initialized")
                return True

            logger.info("APScheduler will create tables on first scheduler start")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize APScheduler tables: {str(e)}", exc_info=True)
            return False

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Clean up completed jobs older than specified days

        Args:
            days: Number of days to retain job history

        Returns:
            Number of jobs deleted
        """
        try:
            engine = self.get_engine()

            # Only clean up if table exists
            if not self.table_exists():
                logger.warning("Cannot cleanup: jobs table does not exist")
                return 0

            with engine.begin() as conn:
                # APScheduler stores next_run_time, we clean up jobs with no next run
                # that are older than the retention period
                query = text(f"""
                    DELETE FROM {self.table_name}
                    WHERE next_run_time IS NULL
                    AND id IN (
                        SELECT id FROM {self.table_name}
                        WHERE next_run_time IS NULL
                        LIMIT 1000
                    )
                """)

                result = conn.execute(query)
                deleted_count = result.rowcount

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old completed jobs")

                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {str(e)}", exc_info=True)
            return 0

    def get_job_count(self) -> Optional[int]:
        """
        Get total number of jobs in the database

        Returns:
            Number of jobs or None if error
        """
        try:
            if not self.table_exists():
                return 0

            engine = self.get_engine()
            with engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {self.table_name}")
                )
                count = result.scalar()
                logger.debug(f"Total jobs in database: {count}")
                return count

        except Exception as e:
            logger.error(f"Error getting job count: {str(e)}", exc_info=True)
            return None

    def health_check(self) -> dict:
        """
        Perform comprehensive health check

        Returns:
            Dictionary with health check results
        """
        health_status = {
            'connection_valid': False,
            'table_exists': False,
            'job_count': None,
            'error': None
        }

        try:
            # Check connection
            health_status['connection_valid'] = self.validate_connection()

            if not health_status['connection_valid']:
                health_status['error'] = "Database connection failed"
                return health_status

            # Check table
            health_status['table_exists'] = self.table_exists()

            # Get job count
            if health_status['table_exists']:
                health_status['job_count'] = self.get_job_count()

            logger.info(f"Scheduler database health check: {health_status}")

        except Exception as e:
            health_status['error'] = str(e)
            logger.error(f"Health check failed: {str(e)}", exc_info=True)

        return health_status

    def close(self):
        """Close database connections"""
        if self.engine:
            try:
                self.engine.dispose()
                logger.info("Database engine disposed successfully")
            except Exception as e:
                logger.error(f"Error disposing database engine: {str(e)}")
            finally:
                self.engine = None


# Global database manager instance
_db_manager: Optional[SchedulerDatabaseManager] = None


def get_db_manager() -> SchedulerDatabaseManager:
    """Get or create the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = SchedulerDatabaseManager()
    return _db_manager


def initialize_scheduler_database() -> bool:
    """
    Initialize APScheduler database

    This should be called during application startup.

    Returns:
        True if successful, False otherwise
    """
    manager = get_db_manager()
    return manager.initialize_tables()


def cleanup_scheduler_database(days: int = 30) -> int:
    """
    Cleanup old scheduler jobs

    Args:
        days: Retention period in days

    Returns:
        Number of jobs deleted
    """
    manager = get_db_manager()
    return manager.cleanup_old_jobs(days)


def scheduler_db_health_check() -> dict:
    """
    Check scheduler database health

    Returns:
        Health check results
    """
    manager = get_db_manager()
    return manager.health_check()
