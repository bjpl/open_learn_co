"""
Pytest configuration and fixtures for the Colombian platform test suite
"""

import pytest
import asyncio
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
import aiohttp
from aioresponses import aioresponses

# Test data and configuration
TEST_CONFIG_DIR = Path(__file__).parent / "test_data"
TEST_CONFIG_DIR.mkdir(exist_ok=True)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_aiohttp():
    """Mock aiohttp responses"""
    with aioresponses() as m:
        yield m


@pytest.fixture
def sample_api_response():
    """Sample API response data"""
    return {
        "status": "success",
        "data": [
            {
                "id": "1",
                "title": "Economic Indicator",
                "value": 3.2,
                "date": "2024-01-15",
                "source": "DANE"
            },
            {
                "id": "2",
                "title": "Inflation Rate",
                "value": 5.8,
                "date": "2024-01-15",
                "source": "Banco de la República"
            }
        ],
        "pagination": {
            "page": 1,
            "total": 2,
            "per_page": 10
        }
    }


@pytest.fixture
def sample_news_articles():
    """Sample scraped news articles"""
    return [
        {
            "title": "Colombia's Economy Shows Growth",
            "content": "The Colombian economy demonstrated positive indicators...",
            "url": "https://eltiempo.com/article/1",
            "published_date": "2024-01-15T10:00:00Z",
            "author": "María García",
            "source": "El Tiempo",
            "category": "economy"
        },
        {
            "title": "New Infrastructure Projects Announced",
            "content": "The government announced several infrastructure projects...",
            "url": "https://elespectador.com/article/2",
            "published_date": "2024-01-15T14:30:00Z",
            "author": "Carlos Rodríguez",
            "source": "El Espectador",
            "category": "politics"
        }
    ]


@pytest.fixture
def mock_html_content():
    """Mock HTML content for scraping tests"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test News Site</title>
    </head>
    <body>
        <article class="article-container">
            <h1 class="titulo">Test Article Title</h1>
            <div class="articulo-contenido">
                <p>This is the article content for testing purposes.</p>
                <p>It contains multiple paragraphs of text.</p>
            </div>
            <div class="metadata">
                <span class="author">Test Author</span>
                <span class="date">2024-01-15</span>
            </div>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def test_sources_config():
    """Test sources configuration"""
    return {
        "government": {
            "dane": {
                "name": "DANE - Test",
                "url": "https://test.dane.gov.co",
                "api_endpoint": "https://test.dane.gov.co/api",
                "type": "statistics",
                "priority": "high",
                "rate_limit": "10/minute",
                "auth_type": "api_key",
                "update_frequency": "daily"
            },
            "banco_republica": {
                "name": "Banco República - Test",
                "url": "https://test.banrep.gov.co",
                "api_endpoint": "https://test.banrep.gov.co/api",
                "type": "economic",
                "priority": "high",
                "rate_limit": "20/minute",
                "auth_type": "none",
                "update_frequency": "daily"
            }
        },
        "media": {
            "national": {
                "el_tiempo": {
                    "name": "El Tiempo - Test",
                    "url": "https://test.eltiempo.com",
                    "type": "news",
                    "priority": "high",
                    "scraping_interval": 30,
                    "selectors": {
                        "article": "article.article-container",
                        "title": "h1.titulo",
                        "content": "div.articulo-contenido"
                    }
                }
            }
        }
    }


@pytest.fixture
def temp_config_file(test_sources_config):
    """Create a temporary configuration file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_sources_config, f)
        return f.name


@pytest.fixture
def mock_database():
    """Mock database connection and operations"""
    db_mock = Mock()
    db_mock.execute = AsyncMock()
    db_mock.fetchall = AsyncMock(return_value=[])
    db_mock.fetchone = AsyncMock(return_value=None)
    db_mock.commit = AsyncMock()
    db_mock.rollback = AsyncMock()
    return db_mock


@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    return redis_mock


@pytest.fixture
def mock_scheduler():
    """Mock APScheduler"""
    scheduler_mock = Mock()
    scheduler_mock.add_job = Mock()
    scheduler_mock.remove_job = Mock()
    scheduler_mock.start = Mock()
    scheduler_mock.shutdown = Mock()
    scheduler_mock.get_jobs = Mock(return_value=[])
    return scheduler_mock


@pytest.fixture
def mock_nlp_pipeline():
    """Mock NLP pipeline for text processing"""
    nlp_mock = Mock()
    nlp_mock.process = Mock(return_value={
        "entities": ["Colombia", "Bogotá", "DANE"],
        "sentiment": {"compound": 0.5, "pos": 0.7, "neu": 0.2, "neg": 0.1},
        "keywords": ["economía", "crecimiento", "inflación"],
        "language": "es"
    })
    return nlp_mock


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter"""
    rate_limiter_mock = AsyncMock()
    rate_limiter_mock.acquire = AsyncMock(return_value=True)
    rate_limiter_mock.is_allowed = AsyncMock(return_value=True)
    return rate_limiter_mock


@pytest.fixture
def api_client_config():
    """Configuration for API clients"""
    return {
        "base_url": "https://test-api.example.com",
        "api_key": "test_api_key_123",
        "timeout": 30,
        "rate_limit": "10/minute",
        "retry_attempts": 3
    }


@pytest.fixture
def scraper_config():
    """Configuration for scrapers"""
    return {
        "base_url": "https://test-news.example.com",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Test Browser)"
        },
        "timeout": 30,
        "rate_limit": "5/minute",
        "selectors": {
            "article": "article",
            "title": "h1",
            "content": "div.content",
            "author": ".author",
            "date": ".date"
        }
    }


@pytest.fixture
def mock_source_manager(temp_config_file):
    """Mock source manager with test configuration"""
    with patch('backend.core.source_manager.SourceManager') as mock_class:
        instance = mock_class.return_value
        instance.config_path = temp_config_file
        instance.sources = {}
        instance.api_clients = {}
        instance.scrapers = {}
        instance.scheduler = Mock()

        # Mock methods
        instance.load_sources = Mock()
        instance.get_sources_by_priority = Mock(return_value=[])
        instance.get_sources_by_category = Mock(return_value=[])
        instance.get_api_sources = Mock(return_value=[])
        instance.get_scraper_sources = Mock(return_value=[])
        instance.initialize_collectors = AsyncMock()
        instance.test_source = AsyncMock()

        yield instance


@pytest.fixture
def mock_session():
    """Mock aiohttp session"""
    session_mock = AsyncMock()

    # Mock response
    response_mock = AsyncMock()
    response_mock.status = 200
    response_mock.json = AsyncMock()
    response_mock.text = AsyncMock()
    response_mock.headers = {}

    session_mock.get = AsyncMock(return_value=response_mock)
    session_mock.post = AsyncMock(return_value=response_mock)
    session_mock.close = AsyncMock()

    return session_mock


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables and paths"""
    import os
    os.environ['TESTING'] = 'true'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['REDIS_URL'] = 'redis://localhost:6379/1'

    # Create test data directory
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    yield

    # Cleanup
    if 'TESTING' in os.environ:
        del os.environ['TESTING']


@pytest.fixture
def sample_government_data():
    """Sample government API data for different sources"""
    return {
        "dane": {
            "indicators": [
                {
                    "indicator_id": "PIB_TRIM",
                    "name": "PIB Trimestral",
                    "value": 234567.89,
                    "period": "2024-Q1",
                    "unit": "Miles de millones COP"
                }
            ]
        },
        "banrep": {
            "exchange_rates": [
                {
                    "currency": "USD",
                    "rate": 4250.50,
                    "date": "2024-01-15"
                }
            ]
        },
        "secop": {
            "contracts": [
                {
                    "contract_id": "COL-2024-001",
                    "title": "Infraestructura Educativa",
                    "amount": 5000000000,
                    "entity": "Ministerio de Educación"
                }
            ]
        }
    }


@pytest.fixture
def mock_validator():
    """Mock data validator"""
    validator_mock = Mock()
    validator_mock.validate_api_response = Mock(return_value=True)
    validator_mock.validate_scraped_content = Mock(return_value=True)
    validator_mock.validate_source_config = Mock(return_value=True)
    return validator_mock


# Utility functions for tests
def create_mock_response(data: Dict[str, Any], status: int = 200):
    """Create a mock HTTP response"""
    response = Mock()
    response.status = status
    response.json = AsyncMock(return_value=data)
    response.text = AsyncMock(return_value=json.dumps(data))
    response.headers = {"Content-Type": "application/json"}
    return response


def assert_valid_news_article(article: Dict[str, Any]):
    """Assert that an article has required fields"""
    required_fields = ["title", "content", "url", "published_date", "source"]
    for field in required_fields:
        assert field in article, f"Missing required field: {field}"
        assert article[field], f"Empty value for field: {field}"


def assert_valid_api_data(data: Dict[str, Any]):
    """Assert that API data has required structure"""
    assert "status" in data or "data" in data, "Missing status or data field"
    if "data" in data:
        assert isinstance(data["data"], (list, dict)), "Data field must be list or dict"