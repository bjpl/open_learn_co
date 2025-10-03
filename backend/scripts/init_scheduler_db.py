#!/usr/bin/env python3
"""
APScheduler Database Initialization Script

This script initializes the PostgreSQL database for APScheduler
and validates the configuration.

Usage:
    python scripts/init_scheduler_db.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.scheduler_db import (
    get_db_manager,
    initialize_scheduler_database,
    scheduler_db_health_check
)
from app.config.settings import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize APScheduler database"""
    print("=" * 80)
    print("APScheduler Database Initialization")
    print("=" * 80)
    print()

    # Display configuration
    print("Configuration:")
    print(f"  Database URL: {settings.DATABASE_URL_SYNC}")
    print(f"  Host: {settings.POSTGRES_HOST}")
    print(f"  Port: {settings.POSTGRES_PORT}")
    print(f"  Database: {settings.POSTGRES_DB}")
    print(f"  User: {settings.POSTGRES_USER}")
    print()

    # Perform health check
    print("Performing database health check...")
    health_status = scheduler_db_health_check()

    print("Health Check Results:")
    print(f"  Connection Valid: {health_status['connection_valid']}")
    print(f"  Table Exists: {health_status['table_exists']}")
    print(f"  Job Count: {health_status['job_count']}")

    if health_status['error']:
        print(f"  Error: {health_status['error']}")
        print()
        print("❌ Health check failed!")
        return 1

    print()

    # Initialize database
    if not health_status['table_exists']:
        print("Initializing APScheduler database tables...")
        success = initialize_scheduler_database()

        if success:
            print("✅ Database initialized successfully!")
            print()
            print("Note: APScheduler will create the 'apscheduler_jobs' table")
            print("      automatically on first scheduler start.")
        else:
            print("❌ Database initialization failed!")
            return 1
    else:
        print("✅ Database already initialized!")

    print()

    # Get database manager for additional info
    db_manager = get_db_manager()

    # Display final status
    print("Final Status:")
    job_count = db_manager.get_job_count()
    print(f"  Jobs in Database: {job_count if job_count is not None else 'N/A'}")

    print()
    print("=" * 80)
    print("Initialization complete! You can now start the scheduler.")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
