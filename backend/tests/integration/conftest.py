"""
Pytest configuration for integration tests
Provides database fixtures and test setup
"""

import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

from backend.app.database.models import Base as ModelsBase
from backend.app.database.vocabulary_models import Base as VocabBase


# Use in-memory SQLite for fast integration tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    # Create all tables from both base models
    ModelsBase.metadata.create_all(bind=engine)
    VocabBase.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    ModelsBase.metadata.drop_all(bind=engine)
    VocabBase.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_spanish_content():
    """Sample Spanish content for testing"""
    return {
        "simple": "Hoy es un día hermoso. El sol brilla.",
        "intermediate": """
            La economía colombiana mostró un crecimiento notable.
            Los expertos están optimistas sobre el futuro.
        """,
        "advanced": """
            El análisis macroeconómico revela tendencias preocupantes
            en la balanza de pagos y el déficit fiscal estructural.
        """,
        "news": """
            Bogotá, 15 de enero - El gobierno anunció nuevas medidas económicas.
            Las reformas incluyen incentivos fiscales para pequeñas empresas.
        """
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    import os
    os.environ['TESTING'] = 'true'
    os.environ['DATABASE_URL'] = TEST_DATABASE_URL

    yield

    # Cleanup
    if 'TESTING' in os.environ:
        del os.environ['TESTING']
