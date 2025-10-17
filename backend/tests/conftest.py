"""
Basic pytest configuration and fixtures
"""
import pytest
import asyncio
from unittest.mock import Mock, patch


@pytest.fixture
def sample_text():
    """Sample Spanish text for testing"""
    return "El presidente de Colombia anunció nuevas medidas económicas."


@pytest.fixture
def sample_html():
    """Sample HTML for testing"""
    return """
    <html>
        <head>
            <title>Test Article</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <article>
                <h1>Test Title</h1>
                <p>Test content here.</p>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    mock_settings = Mock()
    mock_settings.USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ]
    mock_settings.REQUEST_TIMEOUT = 30
    return mock_settings


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch, mock_settings):
    """Automatically patch settings for all tests"""
    import sys
    if 'app.config' not in sys.modules:
        # Create a mock module
        from types import ModuleType
        config_module = ModuleType('config')
        config_module.settings = mock_settings
        sys.modules['app.config'] = config_module
    else:
        monkeypatch.setattr('app.config.settings', mock_settings)
