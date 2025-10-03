"""
Database connection and session management with production-grade connection pooling
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager, asynccontextmanager
from typing import Optional
import logging
import os

from app.config import settings
from app.database.models import Base

logger = logging.getLogger(__name__)

# Database URL configuration
database_url_async = settings.DATABASE_URL
database_url_sync = settings.DATABASE_URL_SYNC

# Connection pool configuration from environment with production defaults
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20" if not settings.DEBUG else "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600" if not settings.DEBUG else "1800"))
DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
DB_COMMAND_TIMEOUT = int(os.getenv("DB_COMMAND_TIMEOUT", "60"))

# Connection pool metrics
pool_metrics = {
    "connections_created": 0,
    "connections_closed": 0,
    "connections_recycled": 0,
    "checkout_count": 0,
    "checkin_count": 0,
    "connection_errors": 0
}


def _on_connect(dbapi_conn, connection_record):
    """Configure connection on creation"""
    pool_metrics["connections_created"] += 1
    logger.debug(f"New connection created. Total: {pool_metrics['connections_created']}")


def _on_checkout(dbapi_conn, connection_record, connection_proxy):
    """Track connection checkouts"""
    pool_metrics["checkout_count"] += 1


def _on_checkin(dbapi_conn, connection_record):
    """Track connection checkins"""
    pool_metrics["checkin_count"] += 1


def _on_close(dbapi_conn, connection_record):
    """Track connection closures"""
    pool_metrics["connections_closed"] += 1
    logger.debug(f"Connection closed. Total closed: {pool_metrics['connections_closed']}")


# Configure engines based on database type
if database_url_sync.startswith("sqlite"):
    # SQLite configuration (development only)
    engine = create_engine(
        database_url_sync,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool  # SQLite uses static pool
    )
    # For SQLite, use aiosqlite for async operations
    async_database_url = database_url_async.replace("sqlite://", "sqlite+aiosqlite://")
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool
    )
else:
    # PostgreSQL configuration with production-grade pooling
    engine = create_engine(
        database_url_sync,
        echo=settings.DEBUG,
        # QueuePool configuration for optimal connection management
        poolclass=pool.QueuePool,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        pool_recycle=DB_POOL_RECYCLE,
        pool_pre_ping=DB_POOL_PRE_PING,
        # Connection arguments
        connect_args={
            "connect_timeout": DB_CONNECT_TIMEOUT,
            "server_settings": {
                "application_name": "colombia_intel_platform"
            }
        },
        # Execution options
        execution_options={
            "isolation_level": "READ COMMITTED"
        }
    )

    # Async engine for PostgreSQL with same pooling configuration
    async_engine = create_async_engine(
        database_url_async,
        echo=settings.DEBUG,
        poolclass=pool.AsyncAdaptedQueuePool,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        pool_recycle=DB_POOL_RECYCLE,
        pool_pre_ping=DB_POOL_PRE_PING,
        connect_args={
            "timeout": DB_CONNECT_TIMEOUT,
            "command_timeout": DB_COMMAND_TIMEOUT,
            "server_settings": {
                "application_name": "colombia_intel_platform_async"
            }
        }
    )

    # Register event listeners for metrics tracking
    event.listen(engine.pool, "connect", _on_connect)
    event.listen(engine.pool, "checkout", _on_checkout)
    event.listen(engine.pool, "checkin", _on_checkin)
    event.listen(engine.pool, "close", _on_close)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)


@contextmanager
def get_db() -> Session:
    """Get synchronous database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_async_db() -> AsyncSession:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create tables if they don't exist"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_db():
    """Close database connections gracefully"""
    try:
        # Dispose async engine
        await async_engine.dispose()
        # Dispose sync engine
        engine.dispose()
        logger.info(f"Database connections closed. Metrics: {pool_metrics}")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
        raise


def check_db_connection() -> bool:
    """Check if database is accessible"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        pool_metrics["connection_errors"] += 1
        return False


async def check_async_db_connection() -> bool:
    """Check if async database is accessible"""
    try:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Async database connection check failed: {str(e)}")
        pool_metrics["connection_errors"] += 1
        return False


def get_pool_status() -> dict:
    """Get current connection pool status"""
    if database_url_sync.startswith("sqlite"):
        return {
            "pool_type": "StaticPool",
            "message": "SQLite uses static pool - metrics not available"
        }

    pool_obj = engine.pool
    return {
        "pool_type": "QueuePool",
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_MAX_OVERFLOW,
        "timeout": DB_POOL_TIMEOUT,
        "recycle": DB_POOL_RECYCLE,
        "size": pool_obj.size(),
        "checked_in": pool_obj.checkedin(),
        "checked_out": pool_obj.checkedout(),
        "overflow": pool_obj.overflow(),
        "metrics": pool_metrics,
        "total_capacity": DB_POOL_SIZE + DB_MAX_OVERFLOW
    }


async def get_async_pool_status() -> dict:
    """Get current async connection pool status"""
    if database_url_async.startswith("sqlite"):
        return {
            "pool_type": "StaticPool",
            "message": "SQLite uses static pool - metrics not available"
        }

    pool_obj = async_engine.pool
    return {
        "pool_type": "AsyncAdaptedQueuePool",
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_MAX_OVERFLOW,
        "timeout": DB_POOL_TIMEOUT,
        "recycle": DB_POOL_RECYCLE,
        "size": pool_obj.size(),
        "checked_in": pool_obj.checkedin(),
        "checked_out": pool_obj.checkedout(),
        "overflow": pool_obj.overflow(),
        "metrics": pool_metrics,
        "total_capacity": DB_POOL_SIZE + DB_MAX_OVERFLOW
    }