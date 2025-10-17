"""
Unit tests for BaseScraper class
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import aiohttp
from aioresponses import aioresponses
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scrapers.base.base_scraper import BaseScraper
from scrapers.base.rate_limiter import RateLimiter


class ConcreteBaseScraper(BaseScraper):
    """Concrete implementation for testing"""

    async def get_article_urls(self):
        """Implementation of abstract method"""
        return ["https://test.com/article1", "https://test.com/article2"]

    def parse_article(self, soup, url):
        """Implementation of abstract method"""
        return {
            "title": "Test Article",
            "content": "Test content",
            "author": "Test Author",
            "published_date": datetime.utcnow()
        }


class TestBaseScraper:
    """Test suite for BaseScraper"""

    @pytest.fixture
    def mock_config(self):
        """Mock source configuration"""
        return {
            "name": "Test Source",
            "url": "https://test.com",
            "category": "test",
            "scrape_interval": 60
        }

    @pytest.fixture
    def scraper(self, mock_config):
        """Create scraper instance"""
        return ConcreteBaseScraper(mock_config)

    def test_initialization(self, scraper, mock_config):
        """Test scraper initialization"""
        assert scraper.name == "Test Source"
        assert scraper.base_url == "https://test.com"
        assert scraper.category == "test"
        assert scraper.scrape_interval == 60
        assert isinstance(scraper.rate_limiter, RateLimiter)
        assert scraper.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, scraper):
        """Test async context manager"""
        assert scraper.session is None

        async with scraper:
            assert scraper.session is not None
            assert isinstance(scraper.session, aiohttp.ClientSession)

        # Session should be closed after context
        assert scraper.session.closed

    @pytest.mark.asyncio
    async def test_fetch_page_success(self, scraper):
        """Test successful page fetching"""
        with aioresponses() as m:
            test_html = "<html><body>Test content</body></html>"
            m.get("https://test.com/page", status=200, body=test_html)

            async with scraper:
                result = await scraper.fetch_page("https://test.com/page")
                assert result == test_html

    @pytest.mark.asyncio
    async def test_fetch_page_404(self, scraper):
        """Test fetching page with 404 error"""
        with aioresponses() as m:
            m.get("https://test.com/missing", status=404)

            async with scraper:
                result = await scraper.fetch_page("https://test.com/missing")
                assert result is None

    @pytest.mark.asyncio
    async def test_fetch_page_timeout(self, scraper):
        """Test fetching page with timeout"""
        with aioresponses() as m:
            # Simulate timeout by raising asyncio.TimeoutError
            m.get("https://test.com/slow", exception=asyncio.TimeoutError())

            async with scraper:
                result = await scraper.fetch_page("https://test.com/slow")
                assert result is None

    @pytest.mark.asyncio
    async def test_fetch_page_rate_limiting(self, scraper):
        """Test that rate limiting is applied"""
        with patch.object(scraper.rate_limiter, 'acquire') as mock_acquire:
            mock_acquire.return_value = None

            with aioresponses() as m:
                m.get("https://test.com/page", status=200, body="test")

                async with scraper:
                    await scraper.fetch_page("https://test.com/page")
                    mock_acquire.assert_called_once()

    def test_parse_html(self, scraper):
        """Test HTML parsing"""
        html = "<html><body><h1>Title</h1></body></html>"
        soup = scraper.parse_html(html)

        assert soup is not None
        assert soup.find('h1').text == "Title"

    def test_generate_content_hash(self, scraper):
        """Test content hash generation"""
        content1 = "This is test content"
        content2 = "This is test content"
        content3 = "Different content"

        hash1 = scraper.generate_content_hash(content1)
        hash2 = scraper.generate_content_hash(content2)
        hash3 = scraper.generate_content_hash(content3)

        # Same content should produce same hash
        assert hash1 == hash2
        # Different content should produce different hash
        assert hash1 != hash3
        # Hash should be 64 characters (SHA256)
        assert len(hash1) == 64

    def test_extract_metadata(self, scraper):
        """Test metadata extraction from HTML"""
        html = """
        <html>
        <head>
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta property="og:image" content="https://test.com/image.jpg">
            <meta name="twitter:card" content="summary">
            <meta name="twitter:site" content="@testsite">
            <meta name="description" content="Page description">
            <meta name="keywords" content="test,keywords,here">
            <meta property="article:published_time" content="2025-01-01T10:00:00Z">
        </head>
        </html>
        """
        soup = scraper.parse_html(html)
        metadata = scraper.extract_metadata(soup)

        assert metadata["og_title"] == "OG Title"
        assert metadata["og_description"] == "OG Description"
        assert metadata["og_image"] == "https://test.com/image.jpg"
        assert metadata["twitter_card"] == "summary"
        assert metadata["twitter_site"] == "@testsite"
        assert metadata["description"] == "Page description"
        assert metadata["keywords"] == ["test", "keywords", "here"]
        assert metadata["published_time"] == "2025-01-01T10:00:00Z"

    def test_clean_text(self, scraper):
        """Test text cleaning functionality"""
        dirty_text = "  This   is\n\n  some\t\tdirty   text\r\n  "
        clean = scraper.clean_text(dirty_text)
        assert clean == "This is some dirty text"

        # Test with None
        assert scraper.clean_text(None) == ""

        # Test with empty string
        assert scraper.clean_text("") == ""

    @pytest.mark.asyncio
    async def test_scrape_full_flow(self, scraper):
        """Test complete scraping flow"""
        with aioresponses() as m:
            # Mock homepage
            homepage_html = """
            <html><body>
                <a href="/article1">Article 1</a>
                <a href="/article2">Article 2</a>
            </body></html>
            """

            # Mock articles
            article1_html = """
            <html>
            <head><title>Article 1</title></head>
            <body><p>Content 1</p></body>
            </html>
            """

            article2_html = """
            <html>
            <head><title>Article 2</title></head>
            <body><p>Content 2</p></body>
            </html>
            """

            m.get("https://test.com", status=200, body=homepage_html)
            m.get("https://test.com/article1", status=200, body=article1_html)
            m.get("https://test.com/article2", status=200, body=article2_html)

            async with scraper:
                results = await scraper.scrape()

                assert len(results) == 2
                for result in results:
                    assert result.source == "Test Source"
                    assert result.category == "test"
                    assert result.content_hash is not None

    @pytest.mark.asyncio
    async def test_scrape_with_error_handling(self, scraper):
        """Test scraping with error scenarios"""
        with aioresponses() as m:
            # Simulate network error
            m.get("https://test.com", exception=aiohttp.ClientError("Network error"))

            async with scraper:
                results = await scraper.scrape()
                # Should handle error gracefully and return empty list
                assert results == []

    def test_abstract_methods_required(self):
        """Test that abstract methods must be implemented"""
        with pytest.raises(TypeError):
            # Should fail because abstract methods not implemented
            class IncompleteScraper(BaseScraper):
                pass

            config = {"name": "test", "url": "test", "category": "test"}
            IncompleteScraper(config)


@pytest.mark.asyncio
class TestBaseScraperPerformance:
    """Performance-related tests for BaseScraper"""

    @pytest.fixture
    def scraper(self):
        config = {
            "name": "Performance Test",
            "url": "https://test.com",
            "category": "test",
            "scrape_interval": 60
        }
        return ConcreteBaseScraper(config)

    @pytest.mark.slow
    async def test_concurrent_fetching(self, scraper):
        """Test concurrent page fetching"""
        urls = [f"https://test.com/page{i}" for i in range(10)]

        with aioresponses() as m:
            for url in urls:
                m.get(url, status=200, body=f"<html>Content for {url}</html>")

            async with scraper:
                # Fetch pages concurrently
                tasks = [scraper.fetch_page(url) for url in urls]
                results = await asyncio.gather(*tasks)

                assert len(results) == 10
                assert all(result is not None for result in results)