"""
APScheduler Service for Automated Scraping
PostgreSQL-backed scheduler with tiered priorities, job recovery, and monitoring
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import (
    EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED,
    EVENT_SCHEDULER_STARTED, EVENT_SCHEDULER_SHUTDOWN
)
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging
import asyncio

from app.config.scheduler_config import (
    SCHEDULER_CONFIG, SCRAPER_TIERS, MONITORING_CONFIG,
    PERSISTENCE_CONFIG, SCHEDULER_TIMEZONE
)
from app.services.scheduler_jobs import (
    setup_scraper_jobs, get_job_status,
    get_scheduler_metrics, cleanup_old_executions
)
from app.services.notification_scheduler_jobs import NOTIFICATION_JOBS
from app.core.scheduler_db import (
    get_db_manager, initialize_scheduler_database,
    scheduler_db_health_check
)

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Manages APScheduler for automated scraping operations
    Features:
    - PostgreSQL persistence for job recovery
    - Tiered scheduling (high/medium/low priority)
    - Automatic retry with exponential backoff
    - Job monitoring and metrics
    - Graceful shutdown with job preservation
    """

    def __init__(self):
        """Initialize scheduler service"""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.running: bool = False
        self.metrics: Dict[str, Any] = {
            'jobs_executed': 0,
            'jobs_failed': 0,
            'jobs_missed': 0,
            'last_execution': None,
            'uptime_start': None
        }
        logger.info("Scheduler service initialized")

    async def start(self) -> None:
        """
        Start the APScheduler with PostgreSQL persistence
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return

        try:
            # Initialize database tables first
            logger.info("Initializing APScheduler database...")
            db_initialized = initialize_scheduler_database()

            if not db_initialized:
                raise RuntimeError("Failed to initialize APScheduler database")

            # Perform health check
            health_status = scheduler_db_health_check()
            logger.info(f"Scheduler database health: {health_status}")

            if not health_status['connection_valid']:
                raise RuntimeError("Database connection validation failed")

            # Create scheduler instance with PostgreSQL jobstore
            logger.info("Creating APScheduler instance with PostgreSQL persistence...")
            self.scheduler = AsyncIOScheduler(**SCHEDULER_CONFIG)

            # Register event listeners
            self._register_event_listeners()

            # Start scheduler
            self.scheduler.start()
            self.running = True
            self.metrics['uptime_start'] = datetime.now(SCHEDULER_TIMEZONE)

            logger.info("APScheduler started successfully with PostgreSQL persistence")

            # Set up all scraper jobs
            await setup_scraper_jobs(self.scheduler)

            # Set up notification jobs
            for job_config in NOTIFICATION_JOBS:
                self.scheduler.add_job(**job_config)
            logger.info(f"Registered {len(NOTIFICATION_JOBS)} notification jobs")

            # Schedule periodic cleanup if enabled
            if PERSISTENCE_CONFIG['enable_job_recovery']:
                self.scheduler.add_job(
                    cleanup_old_executions,
                    'interval',
                    hours=24,
                    id='cleanup_old_executions',
                    replace_existing=True,
                    next_run_time=datetime.now(SCHEDULER_TIMEZONE) + timedelta(hours=1)
                )

            logger.info(f"Scheduler started with {len(self.scheduler.get_jobs())} jobs")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
            raise

    async def shutdown(self, wait: bool = True) -> None:
        """
        Gracefully shutdown scheduler

        Args:
            wait: If True, wait for running jobs to complete
        """
        if not self.running:
            logger.warning("Scheduler is not running")
            return

        try:
            logger.info("Shutting down scheduler...")

            if self.scheduler:
                # Shutdown scheduler (jobs are persisted in PostgreSQL)
                self.scheduler.shutdown(wait=wait)
                self.running = False

                logger.info("Scheduler shutdown complete - jobs persisted to PostgreSQL")

            # Clean up database connections
            db_manager = get_db_manager()
            db_manager.close()
            logger.info("Database connections closed")

        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {str(e)}", exc_info=True)

    def _register_event_listeners(self) -> None:
        """Register event listeners for monitoring"""

        def job_executed(event):
            """Handle successful job execution"""
            self.metrics['jobs_executed'] += 1
            self.metrics['last_execution'] = datetime.now(SCHEDULER_TIMEZONE)
            logger.debug(f"Job {event.job_id} executed successfully")

        def job_error(event):
            """Handle job execution errors"""
            self.metrics['jobs_failed'] += 1
            logger.error(
                f"Job {event.job_id} failed: {event.exception}",
                exc_info=event.exception
            )

        def job_missed(event):
            """Handle missed job executions"""
            self.metrics['jobs_missed'] += 1
            logger.warning(f"Job {event.job_id} missed execution")

        def scheduler_started(event):
            """Handle scheduler start"""
            logger.info("Scheduler started event received")

        def scheduler_shutdown(event):
            """Handle scheduler shutdown"""
            logger.info("Scheduler shutdown event received")

        # Register listeners
        self.scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(job_missed, EVENT_JOB_MISSED)
        self.scheduler.add_listener(scheduler_started, EVENT_SCHEDULER_STARTED)
        self.scheduler.add_listener(scheduler_shutdown, EVENT_SCHEDULER_SHUTDOWN)

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status and statistics

        Returns:
            Dictionary with scheduler status information
        """
        if not self.scheduler:
            return {
                'status': 'not_initialized',
                'running': False
            }

        jobs = self.scheduler.get_jobs()

        # Calculate uptime
        uptime_seconds = None
        if self.metrics['uptime_start']:
            uptime_seconds = (
                datetime.now(SCHEDULER_TIMEZONE) - self.metrics['uptime_start']
            ).total_seconds()

        return {
            'status': 'running' if self.running else 'stopped',
            'running': self.running,
            'total_jobs': len(jobs),
            'metrics': {
                **self.metrics,
                'uptime_seconds': uptime_seconds
            },
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                for job in jobs
            ],
            'timestamp': datetime.now(SCHEDULER_TIMEZONE).isoformat()
        }

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific job

        Args:
            job_id: Job identifier

        Returns:
            Job details or None if not found
        """
        if not self.scheduler:
            return None

        job = self.scheduler.get_job(job_id)
        if not job:
            return None

        return {
            'id': job.id,
            'name': job.name,
            'func': f"{job.func.__module__}.{job.func.__name__}",
            'trigger': str(job.trigger),
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'args': job.args,
            'kwargs': job.kwargs,
            'max_instances': job.max_instances,
            'misfire_grace_time': job.misfire_grace_time
        }

    def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job

        Args:
            job_id: Job identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.scheduler:
            return False

        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job {job_id} paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {str(e)}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job

        Args:
            job_id: Job identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.scheduler:
            return False

        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job {job_id} resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {str(e)}")
            return False

    async def trigger_job(self, job_id: str) -> bool:
        """
        Manually trigger a job execution

        Args:
            job_id: Job identifier

        Returns:
            True if triggered successfully
        """
        if not self.scheduler:
            return False

        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now(SCHEDULER_TIMEZONE))
                logger.info(f"Job {job_id} triggered manually")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {str(e)}")
            return False


# Global scheduler instance
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """Get or create the global scheduler service instance"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service


async def start_scheduler() -> None:
    """Start the background scheduler"""
    scheduler = get_scheduler_service()
    await scheduler.start()


async def stop_scheduler(wait: bool = True) -> None:
    """Stop the background scheduler"""
    scheduler = get_scheduler_service()
    await scheduler.shutdown(wait=wait)
