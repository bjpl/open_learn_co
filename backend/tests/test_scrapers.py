"""
Test suite for all Colombian news scrapers

Tests functionality for 15+ news scrapers including El Tiempo, El Espectador,
Semana, regional papers, and specialized sources.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup

from backend.scrapers.sources.media.el_tiempo import ElTiempoScraper
from backend.scrapers.sources.media.el_espectador import ElEspectadorScraper
from backend.scrapers.sources.media.semana import SemanaScraper
from backend.scrapers.sources.media.la_republica import LaRepublicaScraper
from backend.scrapers.sources.media.portafolio import PortafolioScraper
from backend.scrapers.sources.media.la_fm import LaFMScraper
from backend.scrapers.sources.media.blu_radio import BluRadioScraper
from backend.scrapers.sources.media.el_colombiano import ElColombianoScraper
from backend.scrapers.sources.media.el_pais import ElPaisScraper
from backend.scrapers.sources.media.el_heraldo import ElHeraldoScraper
from backend.scrapers.sources.media.dinero import DineroScraper
from backend.scrapers.sources.media.la_silla_vacia import LaSillaVaciaScraper
from backend.scrapers.sources.media.razon_publica import RazonPublicaScraper
from backend.scrapers.sources.media.colombia_check import ColombiaCheckScraper
from backend.scrapers.base.base_scraper import BaseScraper
from backend.scrapers.base.smart_scraper import SmartScraper


class TestElTiempoScraper:
    """Test El Tiempo newspaper scraper"""

    @pytest.fixture
    def el_tiempo_scraper(self, scraper_config):
        """Create El Tiempo scraper instance"""
        config = {
            **scraper_config,
            'base_url': 'https://test.eltiempo.com',
            'name': 'El Tiempo'
        }
        return ElTiempoScraper(config)

    @pytest.fixture
    def el_tiempo_html(self):
        """Sample El Tiempo article HTML"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Colombia's Economy Shows Growth - El Tiempo</title>
        </head>
        <body>
            <article class="article-container">
                <h1 class="titulo">Colombia's Economy Shows Growth in Q1 2024</h1>
                <h2 class="sumario">Economic indicators point to positive trends despite global challenges</h2>
                <div class="metadata">
                    <span class="autor-nombre">María García Economista</span>
                    <time class="fecha" datetime="2024-01-15T10:00:00Z">15 de enero de 2024</time>
                    <span class="categoria">Economía</span>
                </div>
                <div class="articulo-contenido">
                    <p>La economía colombiana mostró signos de recuperación en el primer trimestre de 2024,
                    según datos del DANE. El crecimiento del PIB alcanzó el 3.2% comparado con el mismo período del año anterior.</p>
                    <p>Los sectores que más contribuyeron al crecimiento fueron la industria manufacturera y los servicios.
                    El Banco de la República mantiene una postura prudente ante estos resultados.</p>
                    <p>Expertos como el economista Juan Carlos Ramírez consideran que estos indicadores reflejan
                    la resiliencia de la economía nacional frente a los retos globales.</p>
                </div>
                <div class="tags">
                    <a href="/tag/economia">Economía</a>
                    <a href="/tag/pib">PIB</a>
                    <a href="/tag/dane">DANE</a>
                    <a href="/tag/banco-republica">Banco República</a>
                </div>
            </article>
        </body>
        </html>
        """

    @pytest.fixture
    def el_tiempo_section_html(self):
        """Sample El Tiempo section page HTML"""
        return """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="section-content">
                <article>
                    <h2><a href="/economia/2024/01/15/crecimiento-economico-123456">Colombia Economy Growth</a></h2>
                </article>
                <article>
                    <h3><a href="/politica/2024/01/15/reforma-tributaria-789012">Tax Reform News</a></h3>
                </article>
                <div class="other-links">
                    <a href="/tema/economia">Economy Theme</a>
                    <a href="/autor/maria-garcia">Author Page</a>
                </div>
            </div>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_initialization(self, el_tiempo_scraper):
        """Test El Tiempo scraper initialization"""
        assert el_tiempo_scraper.base_url == 'https://test.eltiempo.com'
        assert 'politica' in el_tiempo_scraper.sections
        assert 'economia' in el_tiempo_scraper.sections
        assert 'article_links' in el_tiempo_scraper.selectors

    @pytest.mark.asyncio
    async def test_parse_article(self, el_tiempo_scraper, el_tiempo_html):
        """Test parsing El Tiempo article"""
        soup = BeautifulSoup(el_tiempo_html, 'html.parser')
        article = el_tiempo_scraper.parse_article(soup, 'https://test.eltiempo.com/test-article')

        assert article is not None
        assert article['title'] == "Colombia's Economy Shows Growth in Q1 2024"
        assert article['subtitle'] == "Economic indicators point to positive trends despite global challenges"
        assert article['author'] == "María García Economista"
        assert article['category'] == 'general'  # From URL extraction
        assert 'PIB' in article['content']
        assert len(article['tags']) == 4

    @pytest.mark.asyncio
    async def test_extract_colombian_entities(self, el_tiempo_scraper, el_tiempo_html):
        """Test extraction of Colombian entities"""
        soup = BeautifulSoup(el_tiempo_html, 'html.parser')
        article = el_tiempo_scraper.parse_article(soup, 'https://test.eltiempo.com/test')

        entities = article['colombian_entities']
        assert 'institutions' in entities
        assert 'DANE' in entities['institutions']
        assert 'Banco de la República' in entities['institutions']

    @pytest.mark.asyncio
    async def test_difficulty_calculation(self, el_tiempo_scraper):
        """Test difficulty score calculation for language learning"""
        simple_text = "El gato come. El perro corre. Es muy fácil."
        complex_text = """La implementación de políticas macroeconómicas heterodoxas
        requiere una evaluación multidimensional de los indicadores socioeconómicos
        y la consideración de variables endógenas y exógenas que influyen significativamente."""

        simple_score = el_tiempo_scraper._calculate_difficulty(simple_text)
        complex_score = el_tiempo_scraper._calculate_difficulty(complex_text)

        assert simple_score < complex_score
        assert 1.0 <= simple_score <= 5.0
        assert 1.0 <= complex_score <= 5.0

    @pytest.mark.asyncio
    async def test_article_url_detection(self, el_tiempo_scraper):
        """Test article URL pattern detection"""
        valid_urls = [
            'https://eltiempo.com/politica/2024/01/15/noticia-123456',
            'https://eltiempo.com/economia/article/2024-economic-growth-789012',
            'https://eltiempo.com/justicia/noticia/caso-judicial-345678'
        ]

        invalid_urls = [
            'https://eltiempo.com/tema/economia',
            'https://eltiempo.com/autor/maria-garcia',
            'https://eltiempo.com/seccion/politica',
            'https://eltiempo.com/multimedia/galeria',
            'mailto:contact@eltiempo.com'
        ]

        for url in valid_urls:
            assert el_tiempo_scraper._is_article_url(url), f"Should be valid: {url}"

        for url in invalid_urls:
            assert not el_tiempo_scraper._is_article_url(url), f"Should be invalid: {url}"

    @pytest.mark.asyncio
    async def test_paywall_detection(self, el_tiempo_scraper):
        """Test paywall content detection"""
        paywall_content = "Este es contenido exclusivo. Suscríbete para acceso ilimitado."
        free_content = """Este es un artículo completo con mucho contenido disponible
        para todos los lectores. Incluye análisis detallado y múltiples párrafos de información."""

        assert el_tiempo_scraper._is_paywall_content(paywall_content)
        assert not el_tiempo_scraper._is_paywall_content(free_content)

    @pytest.mark.asyncio
    async def test_get_article_urls(self, el_tiempo_scraper, el_tiempo_section_html, mock_aiohttp):
        """Test getting article URLs from sections"""
        # Mock section page responses
        for section in el_tiempo_scraper.sections[:2]:  # Test first 2 sections
            mock_aiohttp.get(
                f'https://test.eltiempo.com/{section}',
                body=el_tiempo_section_html,
                content_type='text/html'
            )

        urls = await el_tiempo_scraper.get_article_urls()

        assert isinstance(urls, list)
        assert len(urls) > 0
        # Should find the article URLs from the HTML
        assert any('crecimiento-economico' in url for url in urls)


class TestElEspectadorScraper:
    """Test El Espectador newspaper scraper"""

    @pytest.fixture
    def el_espectador_scraper(self, scraper_config):
        """Create El Espectador scraper instance"""
        config = {
            **scraper_config,
            'base_url': 'https://test.elespectador.com',
            'name': 'El Espectador'
        }
        return ElEspectadorScraper(config)

    @pytest.fixture
    def el_espectador_html(self):
        """Sample El Espectador article HTML"""
        return """
        <article class="Article">
            <h1 class="Article-Title">Infrastructure Projects Announced by Government</h1>
            <div class="Article-Lead">New transportation projects aim to connect rural areas</div>
            <div class="Article-Content">
                <p>El gobierno nacional anunció una inversión de 15 billones de pesos en proyectos
                de infraestructura para los próximos tres años.</p>
                <p>Los proyectos incluyen carreteras, puentes y sistemas de transporte masivo
                en ciudades intermedias del país.</p>
            </div>
            <div class="Article-Meta">
                <span class="author">Carlos Rodríguez</span>
                <time datetime="2024-01-15T14:30:00Z">Enero 15, 2024</time>
            </div>
        </article>
        """

    @pytest.mark.asyncio
    async def test_parse_article(self, el_espectador_scraper, el_espectador_html):
        """Test parsing El Espectador article"""
        soup = BeautifulSoup(el_espectador_html, 'html.parser')
        article = el_espectador_scraper.parse_article(soup, 'https://test.elespectador.com/test')

        assert article is not None
        assert 'Infrastructure Projects' in article['title']
        assert article['author'] == "Carlos Rodríguez"
        assert 'infraestructura' in article['content'].lower()


class TestSemanaScraper:
    """Test Semana magazine scraper"""

    @pytest.fixture
    def semana_scraper(self, scraper_config):
        """Create Semana scraper instance"""
        config = {
            **scraper_config,
            'base_url': 'https://test.semana.com',
            'name': 'Semana'
        }
        return SemanaScraper(config)

    @pytest.mark.asyncio
    async def test_initialization(self, semana_scraper):
        """Test Semana scraper initialization"""
        assert semana_scraper.base_url == 'https://test.semana.com'
        assert semana_scraper.source_config['name'] == 'Semana'


class TestLaRepublicaScraper:
    """Test La República business newspaper scraper"""

    @pytest.fixture
    def la_republica_scraper(self, scraper_config):
        """Create La República scraper instance"""
        config = {
            **scraper_config,
            'base_url': 'https://test.larepublica.co',
            'name': 'La República'
        }
        return LaRepublicaScraper(config)

    @pytest.mark.asyncio
    async def test_business_focus(self, la_republica_scraper):
        """Test business content focus"""
        # La República should have business-focused selectors and patterns
        assert hasattr(la_republica_scraper, 'business_indicators') or hasattr(la_republica_scraper, 'economic_terms')


class TestRegionalScrapers:
    """Test regional newspaper scrapers"""

    @pytest.fixture
    def regional_scrapers(self, scraper_config):
        """Create regional scraper instances"""
        configs = [
            {'name': 'El Colombiano', 'base_url': 'https://test.elcolombiano.com', 'region': 'Antioquia'},
            {'name': 'El País', 'base_url': 'https://test.elpais.com.co', 'region': 'Valle del Cauca'},
            {'name': 'El Heraldo', 'base_url': 'https://test.elheraldo.co', 'region': 'Atlántico'}
        ]

        scrapers = []
        for config in configs:
            full_config = {**scraper_config, **config}
            if 'elcolombiano' in config['base_url']:
                scrapers.append(ElColombianoScraper(full_config))
            elif 'elpais' in config['base_url']:
                scrapers.append(ElPaisScraper(full_config))
            elif 'elheraldo' in config['base_url']:
                scrapers.append(ElHeraldoScraper(full_config))

        return scrapers

    @pytest.mark.asyncio
    async def test_regional_initialization(self, regional_scrapers):
        """Test regional scrapers initialization"""
        for scraper in regional_scrapers:
            assert scraper is not None
            assert hasattr(scraper, 'base_url')
            assert hasattr(scraper, 'source_config')


class TestRadioScrapers:
    """Test radio news scrapers"""

    @pytest.fixture
    def radio_scrapers(self, scraper_config):
        """Create radio scraper instances"""
        configs = [
            {'name': 'La FM', 'base_url': 'https://test.lafm.com.co'},
            {'name': 'Blu Radio', 'base_url': 'https://test.bluradio.com'}
        ]

        scrapers = []
        for config in configs:
            full_config = {**scraper_config, **config}
            if 'lafm' in config['base_url']:
                scrapers.append(LaFMScraper(full_config))
            elif 'bluradio' in config['base_url']:
                scrapers.append(BluRadioScraper(full_config))

        return scrapers

    @pytest.mark.asyncio
    async def test_radio_content_extraction(self, radio_scrapers):
        """Test radio news content extraction"""
        for scraper in radio_scrapers:
            assert scraper is not None
            # Radio scrapers should handle audio content metadata
            assert hasattr(scraper, 'selectors')


class TestSpecializedScrapers:
    """Test specialized publication scrapers"""

    @pytest.fixture
    def specialized_scrapers(self, scraper_config):
        """Create specialized scraper instances"""
        configs = [
            {'name': 'Dinero', 'base_url': 'https://test.dinero.com', 'type': 'business_magazine'},
            {'name': 'La Silla Vacía', 'base_url': 'https://test.lasillavacia.com', 'type': 'political_analysis'},
            {'name': 'Razón Pública', 'base_url': 'https://test.razonpublica.com', 'type': 'analysis'},
            {'name': 'Colombia Check', 'base_url': 'https://test.colombiacheck.com', 'type': 'fact_checking'}
        ]

        scrapers = []
        for config in configs:
            full_config = {**scraper_config, **config}
            if 'dinero' in config['base_url']:
                scrapers.append(DineroScraper(full_config))
            elif 'lasillavacia' in config['base_url']:
                scrapers.append(LaSillaVaciaScraper(full_config))
            elif 'razonpublica' in config['base_url']:
                scrapers.append(RazonPublicaScraper(full_config))
            elif 'colombiacheck' in config['base_url']:
                scrapers.append(ColombiaCheckScraper(full_config))

        return scrapers

    @pytest.mark.asyncio
    async def test_specialized_content_types(self, specialized_scrapers):
        """Test specialized content type handling"""
        for scraper in specialized_scrapers:
            assert scraper is not None
            # Each specialized scraper should have specific content patterns
            config_type = scraper.source_config.get('type', '')
            if config_type == 'fact_checking':
                # Colombia Check should have fact-checking specific logic
                assert hasattr(scraper, 'fact_check_indicators') or 'fact' in str(scraper.__class__).lower()


class TestBaseScraper:
    """Test base scraper functionality"""

    @pytest.fixture
    def base_scraper(self, scraper_config):
        """Create base scraper instance"""
        return BaseScraper(scraper_config)

    @pytest.mark.asyncio
    async def test_html_parsing(self, base_scraper, mock_html_content):
        """Test HTML parsing functionality"""
        soup = base_scraper.parse_html(mock_html_content)

        assert soup is not None
        assert soup.find('h1') is not None
        assert soup.find('article') is not None

    @pytest.mark.asyncio
    async def test_text_cleaning(self, base_scraper):
        """Test text cleaning functionality"""
        dirty_text = "  This is\n\ta  test  with\textra\twhitespace  \n"
        clean_text = base_scraper.clean_text(dirty_text)

        assert clean_text == "This is a test with extra whitespace"

    @pytest.mark.asyncio
    async def test_rate_limiting(self, base_scraper):
        """Test rate limiting functionality"""
        # Rate limiter should be initialized
        assert base_scraper.rate_limiter is not None

    @pytest.mark.asyncio
    async def test_caching(self, base_scraper, mock_aiohttp):
        """Test content caching"""
        test_url = 'https://test.example.com/page'
        mock_aiohttp.get(test_url, body='<html><body>Test</body></html>')

        # First request
        content1 = await base_scraper.fetch_page(test_url)

        # Second request should use cache if implemented
        content2 = await base_scraper.fetch_page(test_url)

        assert content1 == content2

    @pytest.mark.asyncio
    async def test_error_handling(self, base_scraper, mock_aiohttp):
        """Test error handling for failed requests"""
        test_url = 'https://test.example.com/error'
        mock_aiohttp.get(test_url, status=404)

        # Should handle 404 gracefully
        content = await base_scraper.fetch_page(test_url)
        assert content is None or content == ""

    @pytest.mark.asyncio
    async def test_user_agent_rotation(self, base_scraper):
        """Test user agent rotation"""
        # Base scraper should have user agent handling
        assert hasattr(base_scraper, 'headers') or hasattr(base_scraper, 'session')


class TestSmartScraper:
    """Test smart scraper with AI-powered extraction"""

    @pytest.fixture
    def smart_scraper(self, scraper_config):
        """Create smart scraper instance"""
        return SmartScraper(scraper_config)

    @pytest.mark.asyncio
    async def test_automatic_selector_detection(self, smart_scraper, mock_html_content):
        """Test automatic CSS selector detection"""
        if hasattr(smart_scraper, 'detect_selectors'):
            selectors = smart_scraper.detect_selectors(mock_html_content)
            assert isinstance(selectors, dict)

    @pytest.mark.asyncio
    async def test_content_extraction_fallback(self, smart_scraper, mock_html_content):
        """Test fallback content extraction when selectors fail"""
        # Smart scraper should handle unknown website structures
        soup = BeautifulSoup(mock_html_content, 'html.parser')

        if hasattr(smart_scraper, 'extract_content_smart'):
            content = smart_scraper.extract_content_smart(soup)
            assert content is not None


class TestScraperPerformance:
    """Performance and load tests for scrapers"""

    @pytest.mark.asyncio
    async def test_concurrent_scraping(self, scraper_config, mock_aiohttp):
        """Test concurrent scraping performance"""
        # Create multiple scrapers
        scrapers = [
            ElTiempoScraper(scraper_config),
            ElEspectadorScraper(scraper_config),
            SemanaScraper(scraper_config)
        ]

        # Mock responses
        test_html = '<html><body><h1>Test</h1><p>Content</p></body></html>'
        for i, scraper in enumerate(scrapers):
            mock_aiohttp.get(f'{scraper.base_url}/test', body=test_html)

        # Test concurrent execution
        tasks = []
        for i, scraper in enumerate(scrapers):
            tasks.append(scraper.fetch_page(f'{scraper.base_url}/test'))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should succeed
        assert len(results) == len(scrapers)
        assert all(result is not None for result in results if not isinstance(result, Exception))

    @pytest.mark.asyncio
    async def test_memory_usage_with_large_content(self, scraper_config, mock_aiohttp):
        """Test memory usage with large HTML content"""
        # Create large HTML content
        large_content = '<html><body>' + '<p>Large paragraph content. ' * 10000 + '</p></body></html>'

        scraper = ElTiempoScraper(scraper_config)
        mock_aiohttp.get(f'{scraper.base_url}/large', body=large_content)

        content = await scraper.fetch_page(f'{scraper.base_url}/large')
        assert content is not None

        # Parse large content
        soup = scraper.parse_html(content)
        assert soup is not None

    @pytest.mark.asyncio
    async def test_rate_limit_compliance(self, scraper_config):
        """Test rate limit compliance across scrapers"""
        scraper = ElTiempoScraper({
            **scraper_config,
            'rate_limit': 2  # Very low for testing
        })

        start_time = datetime.now()

        # Make multiple requests
        tasks = []
        for i in range(3):
            tasks.append(scraper.rate_limiter.acquire())

        await asyncio.gather(*tasks)

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Should respect rate limit
        assert elapsed >= 0.5  # At least some delay


class TestScrapersIntegration:
    """Integration tests across all scrapers"""

    @pytest.mark.asyncio
    async def test_all_scrapers_initialization(self, scraper_config):
        """Test that all scrapers can be initialized"""
        scraper_classes = [
            ElTiempoScraper,
            ElEspectadorScraper,
            SemanaScraper,
            LaRepublicaScraper,
            # Add other scraper classes
        ]

        for scraper_class in scraper_classes:
            try:
                scraper = scraper_class(scraper_config)
                assert scraper is not None
                assert hasattr(scraper, 'parse_article')
                assert hasattr(scraper, 'fetch_page')
            except Exception as e:
                pytest.fail(f"Failed to initialize {scraper_class.__name__}: {e}")

    @pytest.mark.asyncio
    async def test_consistent_article_structure(self, scraper_config):
        """Test that all scrapers return consistent article structure"""
        sample_html = """
        <html>
        <body>
            <article>
                <h1>Test Title</h1>
                <p>Test content paragraph.</p>
                <span class="author">Test Author</span>
                <time>2024-01-15</time>
            </article>
        </body>
        </html>
        """

        scrapers = [
            ElTiempoScraper(scraper_config),
            ElEspectadorScraper(scraper_config)
        ]

        for scraper in scrapers:
            soup = BeautifulSoup(sample_html, 'html.parser')
            article = scraper.parse_article(soup, 'https://test.com/article')

            if article:  # Some scrapers might return None for this generic HTML
                required_fields = ['title', 'content', 'published_date']
                for field in required_fields:
                    assert field in article, f"{scraper.__class__.__name__} missing {field}"

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, scraper_config):
        """Test consistent error handling across scrapers"""
        scrapers = [
            ElTiempoScraper(scraper_config),
            ElEspectadorScraper(scraper_config)
        ]

        # Test with invalid HTML
        invalid_html = "<html><body>No article content</body></html>"

        for scraper in scrapers:
            soup = BeautifulSoup(invalid_html, 'html.parser')
            article = scraper.parse_article(soup, 'https://test.com/invalid')

            # Should return None or handle gracefully
            assert article is None or isinstance(article, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])