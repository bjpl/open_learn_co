"""
Verification test to ensure scraper testing infrastructure is working
"""
import pytest
import sys
import os
from pathlib import Path

# Skip the backend/tests/conftest.py to avoid conflicts
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_imports_work():
    """Verify that we can import scraper modules"""
    # Try importing the modules
    try:
        from scrapers.base.base_scraper import BaseScraper
        from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument
        from scrapers.base.rate_limiter import RateLimiter, DomainRateLimiter
        assert BaseScraper is not None
        assert SmartScraper is not None
        assert RateLimiter is not None
        print("✅ All scraper imports successful")
    except ImportError as e:
        pytest.fail(f"Failed to import scrapers: {e}")


def test_aioresponses_available():
    """Verify aioresponses is installed and working"""
    try:
        from aioresponses import aioresponses
        assert aioresponses is not None
        print("✅ aioresponses is available")
    except ImportError:
        pytest.fail("aioresponses is not installed. Run: pip install aioresponses")


def test_pytest_asyncio_available():
    """Verify pytest-asyncio is installed"""
    try:
        import pytest_asyncio
        assert pytest_asyncio is not None
        print("✅ pytest-asyncio is available")
    except ImportError:
        pytest.fail("pytest-asyncio is not installed. Run: pip install pytest-asyncio")


@pytest.mark.asyncio
async def test_async_test_works():
    """Verify async tests work properly"""
    import asyncio
    await asyncio.sleep(0.01)
    assert True
    print("✅ Async tests are working")


if __name__ == "__main__":
    # Run this file directly to verify setup
    pytest.main([__file__, "-v", "-s"])