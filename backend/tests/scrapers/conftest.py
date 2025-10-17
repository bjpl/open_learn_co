"""
Shared fixtures for scraper tests
"""
import pytest
import asyncio
from typing import AsyncGenerator
import aiohttp
from aioresponses import aioresponses
from unittest.mock import Mock, patch
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))


@pytest.fixture
def mock_aioresponse():
    """Mock aiohttp responses for testing"""
    with aioresponses() as m:
        yield m


@pytest.fixture
async def aiohttp_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Provide an aiohttp session for testing"""
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture
def sample_html():
    """Sample HTML content for testing"""
    return """
    <html>
    <head>
        <title>Test Article - El Tiempo</title>
        <meta property="og:title" content="Test Article" />
        <meta property="og:description" content="This is a test article" />
        <meta property="og:image" content="https://example.com/image.jpg" />
        <meta name="description" content="Test article description" />
        <meta name="keywords" content="test, article, colombia" />
        <meta property="article:published_time" content="2025-10-17T10:00:00Z" />
    </head>
    <body>
        <article>
            <h1>Test Article Title</h1>
            <div class="author">John Doe</div>
            <div class="date">October 17, 2025</div>
            <div class="content">
                <p>This is the first paragraph of test content.</p>
                <p>This is the second paragraph with more details.</p>
            </div>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def sample_homepage_html():
    """Sample homepage HTML with article links"""
    return """
    <html>
    <body>
        <div class="articles">
            <article>
                <h2><a href="/article-1">Article 1 Title</a></h2>
                <p>Article 1 summary</p>
            </article>
            <article>
                <h2><a href="/article-2">Article 2 Title</a></h2>
                <p>Article 2 summary</p>
            </article>
            <article>
                <h2><a href="/article-3">Article 3 Title</a></h2>
                <p>Article 3 summary</p>
            </article>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_source_config():
    """Mock source configuration"""
    return {
        "name": "Test Source",
        "url": "https://test-source.com",
        "category": "test",
        "scrape_interval": 60
    }


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for caching tests"""
    mock = Mock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.ping.return_value = True
    return mock


@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()