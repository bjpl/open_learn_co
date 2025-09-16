"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager, asynccontextmanager
import logging

from app.config import settings
from app.database.models import Base

logger = logging.getLogger(__name__)

# Database URL configuration
database_url = settings.get_database_url

# Configure engines based on database type
if database_url.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        database_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )
    # For SQLite, use aiosqlite for async operations
    async_database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        database_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    async_engine = create_async_engine(
        database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

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
    """Close database connections"""
    await async_engine.dispose()
    logger.info("Database connections closed")


def check_db_connection() -> bool:
    """Check if database is accessible"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False