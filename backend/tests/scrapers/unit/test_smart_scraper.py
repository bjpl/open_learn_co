"""
Unit tests for SmartScraper class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime
import time
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument, RateLimiter


class ConcreteSmartScraper(SmartScraper):
    """Concrete implementation for testing"""

    def extract_article_urls(self, homepage_html):
        """Extract URLs from homepage"""
        # Simple implementation for testing
        return [
            "https://test.com/article1",
            "https://test.com/article2",
            "https://test.com/article3"
        ]

    def extract_article_content(self, article_html, url):
        """Extract content from article"""
        return ScrapedDocument(
            source="Test Source",
            source_type="test",
            url=url,
            title="Test Article",
            content="This is test content for the article.",
            author="Test Author",
            published_date=datetime(2025, 1, 1),
            language="es",
            region="Colombia"
        )


class TestScrapedDocument:
    """Test ScrapedDocument dataclass"""

    def test_document_initialization(self):
        """Test document creation with required fields"""
        doc = ScrapedDocument(
            source="Test",
            source_type="test",
            url="https://test.com",
            title="Title",
            content="Content"
        )

        assert doc.source == "Test"
        assert doc.source_type == "test"
        assert doc.url == "https://test.com"
        assert doc.title == "Title"
        assert doc.content == "Content"
        assert doc.author is None
        assert doc.published_date is None
        assert doc.scraped_at is not None  # Auto-set
        assert doc.metadata == {}  # Default
        assert doc.categories == []  # Default

    def test_document_to_dict(self):
        """Test document conversion to dictionary"""
        now = datetime.utcnow()
        doc = ScrapedDocument(
            source="Test",
            source_type="test",
            url="https://test.com",
            title="Title",
            content="Content",
            published_date=now,
            scraped_at=now
        )

        doc_dict = doc.to_dict()

        assert doc_dict["source"] == "Test"
        assert doc_dict["title"] == "Title"
        assert doc_dict["published_date"] == now.isoformat()
        assert doc_dict["scraped_at"] == now.isoformat()


class TestRateLimiterInSmartScraper:
    """Test RateLimiter implementation in smart_scraper.py"""

    def test_rate_limiter_initialization(self):
        """Test rate limiter with different rate strings"""
        # Per second
        limiter1 = RateLimiter("10/second")
        assert limiter1.max_requests == 10
        assert limiter1.period == 1

        # Per minute
        limiter2 = RateLimiter("60/minute")
        assert limiter2.max_requests == 60
        assert limiter2.period == 60

        # Per hour
        limiter3 = RateLimiter("1000/hour")
        assert limiter3.max_requests == 1000
        assert limiter3.period == 3600

    def test_rate_limiter_acquire(self):
        """Test token acquisition"""
        limiter = RateLimiter("2/second")

        # First two requests should be immediate
        assert limiter.acquire() is True
        assert limiter.acquire() is True

        # Third request should wait (mocked)
        with patch('time.sleep') as mock_sleep:
            assert limiter.acquire() is True
            mock_sleep.assert_called_once()


class TestSmartScraper:
    """Test suite for SmartScraper"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        return {
            "name": "Test Source",
            "url": "https://test.com",
            "rate_limit": "10/minute"
        }

    @pytest.fixture
    def scraper(self, mock_config):
        """Create scraper instance"""
        with patch('redis.Redis') as mock_redis:
            # Mock Redis to be unavailable
            mock_redis.side_effect = Exception("Redis not available")
            return ConcreteSmartScraper(mock_config)

    def test_initialization(self, scraper):
        """Test scraper initialization"""
        assert scraper.source_name == "Test Source"
        assert scraper.base_url == "https://test.com"
        assert scraper.rate_limiter is not None
        assert scraper.session is not None
        assert scraper.cache_enabled is False  # Redis not available

    @patch('redis.Redis')
    def test_initialization_with_redis(self, mock_redis_class, mock_config):
        """Test initialization with Redis available"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        scraper = ConcreteSmartScraper(mock_config)

        assert scraper.cache_enabled is True
        mock_redis.ping.assert_called_once()

    def test_create_session(self, scraper):
        """Test session creation with retry strategy"""
        session = scraper._create_session()

        assert isinstance(session, requests.Session)
        # Check headers are set
        assert "User-Agent" in session.headers
        assert "Accept-Language" in session.headers

    def test_get_cache_key(self, scraper):
        """Test cache key generation"""
        url = "https://test.com/article"
        key = scraper._get_cache_key(url)

        assert key.startswith("scraper:Test Source:")
        # Same URL should produce same key
        assert key == scraper._get_cache_key(url)

    @patch('redis.Redis')
    def test_get_cached(self, mock_redis_class, mock_config):
        """Test getting cached content"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = "<html>Cached content</html>"
        mock_redis_class.return_value = mock_redis

        scraper = ConcreteSmartScraper(mock_config)
        cached = scraper._get_cached("https://test.com/article")

        assert cached == "<html>Cached content</html>"
        mock_redis.get.assert_called_once()

    @patch('redis.Redis')
    def test_set_cache(self, mock_redis_class, mock_config):
        """Test setting cache"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        scraper = ConcreteSmartScraper(mock_config)
        scraper._set_cache("https://test.com/article", "<html>Content</html>", ttl=1800)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 1800  # TTL
        assert call_args[2] == "<html>Content</html>"  # Content

    @patch('requests.Session.get')
    def test_fetch_page_success(self, mock_get, scraper):
        """Test successful page fetching"""
        mock_response = Mock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scraper.fetch_page("https://test.com/page")

        assert result == "<html>Test content</html>"
        mock_get.assert_called_once_with("https://test.com/page", timeout=30)

    @patch('requests.Session.get')
    def test_fetch_page_with_error(self, mock_get, scraper):
        """Test page fetching with error"""
        mock_get.side_effect = requests.RequestException("Network error")

        result = scraper.fetch_page("https://test.com/page")

        assert result is None

    @patch('requests.Session.get')
    def test_fetch_page_with_rate_limiting(self, mock_get, scraper):
        """Test that rate limiting is applied"""
        mock_response = Mock()
        mock_response.text = "content"
        mock_get.return_value = mock_response

        with patch.object(scraper.rate_limiter, 'acquire') as mock_acquire:
            mock_acquire.return_value = True
            scraper.fetch_page("https://test.com/page")
            mock_acquire.assert_called_once()

    def test_parse_html(self, scraper):
        """Test HTML parsing"""
        html = "<html><body><h1>Title</h1></body></html>"
        soup = scraper.parse_html(html)

        assert soup is not None
        assert soup.find('h1').text == "Title"

    @patch.object(ConcreteSmartScraper, 'fetch_page')
    def test_scrape_homepage(self, mock_fetch, scraper):
        """Test homepage scraping for URLs"""
        mock_fetch.return_value = "<html>Homepage content</html>"

        urls = scraper.scrape_homepage()

        assert len(urls) == 3
        assert urls[0] == "https://test.com/article1"
        mock_fetch.assert_called_once_with("https://test.com")

    @patch.object(ConcreteSmartScraper, 'fetch_page')
    def test_scrape_article(self, mock_fetch, scraper):
        """Test single article scraping"""
        mock_fetch.return_value = "<html><body>Article content</body></html>"

        doc = scraper.scrape_article("https://test.com/article1")

        assert isinstance(doc, ScrapedDocument)
        assert doc.title == "Test Article"
        assert doc.url == "https://test.com/article1"

    @patch.object(ConcreteSmartScraper, 'scrape_homepage')
    @patch.object(ConcreteSmartScraper, 'scrape_article')
    def test_scrape_batch(self, mock_scrape_article, mock_scrape_homepage, scraper):
        """Test batch scraping"""
        mock_scrape_homepage.return_value = [
            "https://test.com/article1",
            "https://test.com/article2",
            "https://test.com/article3"
        ]

        mock_scrape_article.return_value = ScrapedDocument(
            source="Test",
            source_type="test",
            url="https://test.com/article",
            title="Test Article",
            content="Content"
        )

        results = scraper.scrape_batch(limit=2)

        assert len(results) == 2
        assert all(isinstance(doc, ScrapedDocument) for doc in results)

    def test_validate_document(self, scraper):
        """Test document validation"""
        # Valid document
        valid_doc = ScrapedDocument(
            source="Test",
            source_type="test",
            url="https://test.com",
            title="Valid Title",
            content="This is valid content with more than 100 characters. " * 3
        )
        assert scraper.validate_document(valid_doc) is True

        # Missing title
        no_title = ScrapedDocument(
            source="Test",
            source_type="test",
            url="https://test.com",
            title="",
            content="Content"
        )
        assert scraper.validate_document(no_title) is False

        # Short content
        short_content = ScrapedDocument(
            source="Test",
            source_type="test",
            url="https://test.com",
            title="Title",
            content="Too short"
        )
        assert scraper.validate_document(short_content) is False


class TestSmartScraperIntegration:
    """Integration tests for SmartScraper"""

    @pytest.mark.integration
    @patch('requests.Session.get')
    def test_full_scraping_flow(self, mock_get):
        """Test complete scraping workflow"""
        # Setup responses
        homepage_response = Mock()
        homepage_response.text = """
        <html><body>
            <a href="/article1">Article 1</a>
            <a href="/article2">Article 2</a>
        </body></html>
        """
        homepage_response.raise_for_status.return_value = None

        article_response = Mock()
        article_response.text = """
        <html>
            <head><title>Article Title</title></head>
            <body><p>Article content here</p></body>
        </html>
        """
        article_response.raise_for_status.return_value = None

        # Configure mock to return different responses
        mock_get.side_effect = [
            homepage_response,  # Homepage
            article_response,   # Article 1
            article_response    # Article 2
        ]

        config = {
            "name": "Integration Test",
            "url": "https://test.com",
            "rate_limit": "100/minute"
        }

        scraper = ConcreteSmartScraper(config)
        results = scraper.scrape_batch(limit=2)

        assert len(results) == 2
        for doc in results:
            assert doc.source == "Test Source"
            assert doc.content is not None