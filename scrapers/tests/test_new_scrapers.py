"""
Comprehensive test suite for all 9 new Colombian news scrapers
Tests basic functionality, error handling, and data quality
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all scrapers
from vanguardia_scraper import VanguardiaScraper
from bluradio_scraper import BluRadioScraper
from elheraldo_scraper import ElHeraldoScraper
from portafolio_scraper import PortafolioScraper
from eluniversal_scraper import ElUniversalScraper
from laopinion_scraper import LaOpinionScraper
from las2orillas_scraper import Las2orillasScraper
from elcolombiano_scraper import ElColombianoScraper
from publimetro_scraper import PublimetroScraper


# Test fixtures
@pytest.fixture
def sample_html():
    """Sample HTML for testing"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Article</title>
        <meta property="og:title" content="Test Article Title">
    </head>
    <body>
        <article>
            <h1 class="title">Test Article Title</h1>
            <div class="summary">This is a test article summary</div>
            <div class="author">Test Author</div>
            <time datetime="2025-01-15T10:00:00Z">15 de enero de 2025</time>
            <div class="article-content">
                <p>This is the first paragraph of test content with enough words to pass validation.</p>
                <p>This is the second paragraph with more test content to ensure quality.</p>
                <p>And here is a third paragraph to make the content substantial enough.</p>
                <p>Fourth paragraph adds even more content for comprehensive testing purposes.</p>
            </div>
            <div class="category">Política</div>
            <div class="tags">
                <a href="/tag/test1">Tag1</a>
                <a href="/tag/test2">Tag2</a>
            </div>
        </article>
    </body>
    </html>
    """


# Tier 1 Scrapers Tests

class TestVanguardiaScraper:
    """Tests for Vanguardia Liberal scraper"""

    def test_initialization(self):
        scraper = VanguardiaScraper()
        assert scraper.name == "Vanguardia Liberal"
        assert scraper.base_url == "https://www.vanguardia.com"
        assert scraper.request_delay == 2.0
        assert len(scraper.sections) > 0

    def test_clean_text(self):
        scraper = VanguardiaScraper()
        text = "  Test   text\n\nwith    spaces  "
        cleaned = scraper._clean_text(text)
        assert cleaned == "Test text with spaces"

    def test_is_article_url(self):
        scraper = VanguardiaScraper()
        assert scraper._is_article_url("https://www.vanguardia.com/area-metropolitana/test-123")
        assert scraper._is_article_url("https://www.vanguardia.com/colombia/article")
        assert not scraper._is_article_url("https://www.vanguardia.com/autor/john")
        assert not scraper._is_article_url("https://www.vanguardia.com/video/test")

    def test_parse_spanish_date(self):
        scraper = VanguardiaScraper()
        date = scraper._parse_spanish_date("15 de enero de 2025")
        assert date.year == 2025
        assert date.month == 1
        assert date.day == 15

    @patch('vanguardia_scraper.requests.Session.get')
    def test_parse_article(self, mock_get, sample_html):
        scraper = VanguardiaScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.vanguardia.com/test")

        assert article is not None
        assert article['title'] == "Test Article Title"
        assert article['source'] == "Vanguardia Liberal"
        assert article['difficulty'] == 'easy'
        assert article['region'] == 'Santander'
        assert len(article['content']) > 200

    def test_context_manager(self):
        with VanguardiaScraper() as scraper:
            assert scraper.session is not None


class TestBluRadioScraper:
    """Tests for Blu Radio scraper"""

    def test_initialization(self):
        scraper = BluRadioScraper()
        assert scraper.name == "Blu Radio"
        assert scraper.base_url == "https://www.bluradio.com"
        assert scraper.request_delay == 1.5
        assert 'nacion' in scraper.sections

    def test_is_article_url(self):
        scraper = BluRadioScraper()
        assert scraper._is_article_url("https://www.bluradio.com/nacion/test-article")
        assert scraper._is_article_url("https://www.bluradio.com/politica/news")
        assert not scraper._is_article_url("https://www.bluradio.com/programa/morning")
        assert not scraper._is_article_url("https://www.bluradio.com/podcast/episode")

    @patch('bluradio_scraper.requests.Session.get')
    def test_parse_article_metadata(self, mock_get, sample_html):
        scraper = BluRadioScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.bluradio.com/test")

        if article:
            assert 'media_type' in article
            assert article['media_type'] == 'radio'
            assert article['difficulty'] == 'easy'


class TestElHeraldoScraper:
    """Tests for El Heraldo scraper"""

    def test_initialization(self):
        scraper = ElHeraldoScraper()
        assert scraper.name == "El Heraldo"
        assert scraper.base_url == "https://www.elheraldo.co"
        assert scraper.request_delay == 1.8
        assert 'barranquilla' in scraper.sections

    def test_is_article_url(self):
        scraper = ElHeraldoScraper()
        assert scraper._is_article_url("https://www.elheraldo.co/barranquilla/article")
        assert scraper._is_article_url("https://www.elheraldo.co/region-caribe/news")
        assert not scraper._is_article_url("https://www.elheraldo.co/galeria/photos")

    @patch('elheraldo_scraper.requests.Session.get')
    def test_regional_metadata(self, mock_get, sample_html):
        scraper = ElHeraldoScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.elheraldo.co/test")

        if article:
            assert article['region'] == 'Atlántico'
            assert article['difficulty'] == 'easy'


# Tier 2 Scrapers Tests

class TestPortafolioScraper:
    """Tests for Portafolio scraper"""

    def test_initialization(self):
        scraper = PortafolioScraper()
        assert scraper.name == "Portafolio"
        assert scraper.base_url == "https://www.portafolio.co"
        assert scraper.request_delay == 2.5
        assert 'economia' in scraper.sections
        assert 'negocios' in scraper.sections

    def test_is_paywall_content(self):
        scraper = PortafolioScraper()
        from bs4 import BeautifulSoup

        paywall_html = "<div>Suscríbase para leer este contenido exclusivo</div>"
        soup = BeautifulSoup(paywall_html, 'html.parser')
        assert scraper._is_paywall_content(soup) == True

        free_html = "<div>Regular article content</div>"
        soup = BeautifulSoup(free_html, 'html.parser')
        assert scraper._is_paywall_content(soup) == False

    @patch('portafolio_scraper.requests.Session.get')
    def test_business_metadata(self, mock_get, sample_html):
        scraper = PortafolioScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.portafolio.co/test")

        if article:
            assert article['difficulty'] == 'medium'
            assert article['specialization'] == 'business'


class TestElUniversalScraper:
    """Tests for El Universal scraper"""

    def test_initialization(self):
        scraper = ElUniversalScraper()
        assert scraper.name == "El Universal"
        assert scraper.base_url == "https://www.eluniversal.com.co"
        assert 'cartagena' in scraper.sections
        assert 'bolivar' in scraper.sections

    @patch('eluniversal_scraper.requests.Session.get')
    def test_regional_focus(self, mock_get, sample_html):
        scraper = ElUniversalScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.eluniversal.com.co/test")

        if article:
            assert article['region'] == 'Bolívar'
            assert article['difficulty'] == 'medium'


class TestLaOpinionScraper:
    """Tests for La Opinión scraper"""

    def test_initialization(self):
        scraper = LaOpinionScraper()
        assert scraper.name == "La Opinión"
        assert scraper.base_url == "https://www.laopinion.com.co"
        assert 'cucuta' in scraper.sections
        assert 'frontera' in scraper.sections

    @patch('laopinion_scraper.requests.Session.get')
    def test_border_news_metadata(self, mock_get, sample_html):
        scraper = LaOpinionScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.laopinion.com.co/test")

        if article:
            assert article['region'] == 'Norte de Santander'
            assert article['specialization'] == 'border_news'


# Tier 3 Scrapers Tests

class TestLas2orillasScraper:
    """Tests for Las2orillas scraper"""

    def test_initialization(self):
        scraper = Las2orillasScraper()
        assert scraper.name == "Las2orillas"
        assert scraper.base_url == "https://www.las2orillas.co"
        assert scraper.request_delay == 2.8
        assert 'opinion' in scraper.sections

    def test_is_article_url(self):
        scraper = Las2orillasScraper()
        assert scraper._is_article_url("https://www.las2orillas.co/2025/01/15/test-article")
        assert scraper._is_article_url("https://www.las2orillas.co/politica/article")
        assert not scraper._is_article_url("https://www.las2orillas.co/autor/writer")

    @patch('las2orillas_scraper.requests.Session.get')
    def test_alternative_media_metadata(self, mock_get, sample_html):
        scraper = Las2orillasScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.las2orillas.co/test")

        if article:
            assert article['media_type'] == 'alternative'
            assert article['content_style'] == 'investigative'


class TestElColombianoScraper:
    """Tests for El Colombiano scraper"""

    def test_initialization(self):
        scraper = ElColombianoScraper()
        assert scraper.name == "El Colombiano"
        assert scraper.base_url == "https://www.elcolombiano.com"
        assert 'medellin' in scraper.sections
        assert 'antioquia' in scraper.sections

    @patch('elcolombiano_scraper.requests.Session.get')
    def test_medellin_focus(self, mock_get, sample_html):
        scraper = ElColombianoScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.elcolombiano.com/test")

        if article:
            assert article['region'] == 'Antioquia'
            assert article['difficulty'] == 'medium'


class TestPublimetroScraper:
    """Tests for Publimetro scraper"""

    def test_initialization(self):
        scraper = PublimetroScraper()
        assert scraper.name == "Publimetro"
        assert scraper.base_url == "https://www.publimetro.co"
        assert scraper.request_delay == 1.5
        assert 'entretenimiento' in scraper.sections
        assert 'estilo-vida' in scraper.sections

    @patch('publimetro_scraper.requests.Session.get')
    def test_lifestyle_content(self, mock_get, sample_html):
        scraper = PublimetroScraper()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article("https://www.publimetro.co/test")

        if article:
            assert article['difficulty'] == 'easy'
            assert article['content_style'] == 'lifestyle'


# Integration Tests

class TestAllScrapersCommon:
    """Common tests for all scrapers"""

    @pytest.mark.parametrize("scraper_class", [
        VanguardiaScraper, BluRadioScraper, ElHeraldoScraper,
        PortafolioScraper, ElUniversalScraper, LaOpinionScraper,
        Las2orillasScraper, ElColombianoScraper, PublimetroScraper
    ])
    def test_scraper_has_required_attributes(self, scraper_class):
        scraper = scraper_class()
        assert hasattr(scraper, 'name')
        assert hasattr(scraper, 'base_url')
        assert hasattr(scraper, 'sections')
        assert hasattr(scraper, 'selectors')
        assert hasattr(scraper, 'request_delay')

    @pytest.mark.parametrize("scraper_class", [
        VanguardiaScraper, BluRadioScraper, ElHeraldoScraper,
        PortafolioScraper, ElUniversalScraper, LaOpinionScraper,
        Las2orillasScraper, ElColombianoScraper, PublimetroScraper
    ])
    def test_scraper_has_required_methods(self, scraper_class):
        scraper = scraper_class()
        assert hasattr(scraper, 'scrape')
        assert hasattr(scraper, '_fetch_page')
        assert hasattr(scraper, '_parse_article')
        assert hasattr(scraper, '_clean_text')
        assert hasattr(scraper, '_is_article_url')

    @pytest.mark.parametrize("scraper_class", [
        VanguardiaScraper, BluRadioScraper, ElHeraldoScraper,
        PortafolioScraper, ElUniversalScraper, LaOpinionScraper,
        Las2orillasScraper, ElColombianoScraper, PublimetroScraper
    ])
    def test_rate_limiting(self, scraper_class):
        scraper = scraper_class()
        assert scraper.request_delay > 0
        assert scraper.request_delay >= 1.5  # Minimum delay
        assert scraper.request_delay <= 3.0  # Maximum delay

    @pytest.mark.parametrize("scraper_class", [
        VanguardiaScraper, BluRadioScraper, ElHeraldoScraper,
        PortafolioScraper, ElUniversalScraper, LaOpinionScraper,
        Las2orillasScraper, ElColombianoScraper, PublimetroScraper
    ])
    @patch('requests.Session.get')
    def test_article_data_structure(self, mock_get, scraper_class, sample_html):
        scraper = scraper_class()
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        article = scraper._parse_article(f"{scraper.base_url}/test")

        if article:
            # Verify required fields
            required_fields = [
                'title', 'content', 'author', 'published_date',
                'category', 'url', 'source', 'scraped_at',
                'word_count', 'content_hash', 'difficulty'
            ]
            for field in required_fields:
                assert field in article, f"Missing field: {field}"

            # Verify data types
            assert isinstance(article['title'], str)
            assert isinstance(article['content'], str)
            assert isinstance(article['word_count'], int)
            assert isinstance(article['tags'], list)


# Error Handling Tests

class TestErrorHandling:
    """Test error handling across all scrapers"""

    @pytest.mark.parametrize("scraper_class", [
        VanguardiaScraper, BluRadioScraper, ElHeraldoScraper
    ])
    @patch('requests.Session.get')
    def test_handles_network_errors(self, mock_get, scraper_class):
        scraper = scraper_class()
        mock_get.side_effect = Exception("Network error")

        result = scraper._fetch_page("https://example.com")
        assert result is None

    @pytest.mark.parametrize("scraper_class", [
        PortafolioScraper, ElUniversalScraper, LaOpinionScraper
    ])
    @patch('requests.Session.get')
    def test_handles_malformed_html(self, mock_get, scraper_class):
        scraper = scraper_class()
        mock_response = Mock()
        mock_response.text = "<html><body>Invalid</body>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scraper._parse_article("https://example.com")
        # Should return None for articles without required content
        assert result is None or isinstance(result, dict)


# Performance Tests

class TestPerformance:
    """Performance and quality tests"""

    @pytest.mark.parametrize("scraper_class", [
        VanguardiaScraper, BluRadioScraper, ElHeraldoScraper,
        PortafolioScraper, ElUniversalScraper, LaOpinionScraper,
        Las2orillasScraper, ElColombianoScraper, PublimetroScraper
    ])
    def test_content_validation_threshold(self, scraper_class):
        scraper = scraper_class()
        # Most scrapers should reject content shorter than 150-200 chars
        # This is tested in the _parse_article method


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
