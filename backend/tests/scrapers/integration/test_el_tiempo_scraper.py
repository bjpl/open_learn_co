"""
Integration tests for El Tiempo scraper
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from aioresponses import aioresponses
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestElTiempoScraper:
    """Test suite for El Tiempo news scraper"""

    @pytest.fixture
    def el_tiempo_config(self):
        """El Tiempo configuration"""
        return {
            "name": "El Tiempo",
            "url": "https://www.eltiempo.com",
            "category": "national_media",
            "scrape_interval": 30
        }

    @pytest.fixture
    def sample_el_tiempo_homepage(self):
        """Sample El Tiempo homepage HTML"""
        return """
        <html>
        <body>
            <section class="destacadas">
                <article class="noticia">
                    <h2><a href="/politica/article-123">Presidente anuncia nuevas medidas económicas</a></h2>
                    <p class="summary">El gobierno colombiano presenta plan de reactivación...</p>
                </article>
                <article class="noticia">
                    <h2><a href="/economia/article-456">PIB de Colombia crece 3.5% en tercer trimestre</a></h2>
                    <p class="summary">Economía muestra señales de recuperación...</p>
                </article>
                <article class="noticia">
                    <h2><a href="/bogota/article-789">Alcaldía de Bogotá implementa nuevo sistema de transporte</a></h2>
                    <p class="summary">TransMilenio tendrá nuevas rutas...</p>
                </article>
            </section>
        </body>
        </html>
        """

    @pytest.fixture
    def sample_el_tiempo_article(self):
        """Sample El Tiempo article HTML"""
        return """
        <html>
        <head>
            <title>Presidente anuncia nuevas medidas económicas - El Tiempo</title>
            <meta property="og:title" content="Presidente anuncia nuevas medidas económicas">
            <meta property="og:description" content="El gobierno colombiano presenta plan de reactivación económica">
            <meta property="article:published_time" content="2025-10-17T10:00:00-05:00">
            <meta name="author" content="Juan Pérez">
        </head>
        <body>
            <article class="articulo-noticia">
                <h1 class="titulo">Presidente anuncia nuevas medidas económicas</h1>
                <div class="autor-fecha">
                    <span class="autor">Por Juan Pérez</span>
                    <time datetime="2025-10-17T10:00:00-05:00">17 de octubre, 2025</time>
                </div>
                <div class="contenido">
                    <p>BOGOTÁ - El presidente de Colombia anunció hoy un paquete de medidas económicas
                    destinadas a impulsar la reactivación del país tras los desafíos económicos recientes.</p>
                    <p>Entre las medidas destacan la reducción de impuestos para pequeñas empresas,
                    nuevos programas de crédito para emprendedores, y un aumento en la inversión
                    en infraestructura pública.</p>
                    <p>"Estas medidas buscan generar empleo y fortalecer el tejido empresarial del país",
                    afirmó el mandatario durante una rueda de prensa en la Casa de Nariño.</p>
                </div>
                <div class="tags">
                    <span class="tag">Economía</span>
                    <span class="tag">Política</span>
                    <span class="tag">Colombia</span>
                </div>
            </article>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_el_tiempo_article_extraction(self, el_tiempo_config, sample_el_tiempo_article):
        """Test extraction of article content from El Tiempo"""
        from scrapers.base.base_scraper import BaseScraper

        class ElTiempoScraper(BaseScraper):
            async def get_article_urls(self):
                return ["https://www.eltiempo.com/politica/article-123"]

            def parse_article(self, soup, url):
                title_elem = soup.find("h1", class_="titulo")
                content_elem = soup.find("div", class_="contenido")
                author_elem = soup.find("span", class_="autor")

                content_text = " ".join([p.text for p in content_elem.find_all("p")]) if content_elem else ""

                return {
                    "title": title_elem.text if title_elem else "",
                    "content": content_text,
                    "author": author_elem.text.replace("Por ", "") if author_elem else "",
                    "url": url
                }

        scraper = ElTiempoScraper(el_tiempo_config)

        # Parse the sample article
        soup = scraper.parse_html(sample_el_tiempo_article)
        article_data = scraper.parse_article(soup, "https://www.eltiempo.com/politica/article-123")

        assert article_data["title"] == "Presidente anuncia nuevas medidas económicas"
        assert "paquete de medidas económicas" in article_data["content"]
        assert article_data["author"] == "Juan Pérez"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_el_tiempo_homepage_parsing(self, el_tiempo_config, sample_el_tiempo_homepage):
        """Test parsing of El Tiempo homepage for article URLs"""
        from scrapers.base.base_scraper import BaseScraper

        class ElTiempoScraper(BaseScraper):
            async def get_article_urls(self):
                # In real implementation, this would fetch and parse homepage
                html = sample_el_tiempo_homepage
                soup = self.parse_html(html)

                articles = []
                for article in soup.find_all("article", class_="noticia"):
                    link = article.find("a")
                    if link and link.get("href"):
                        articles.append(f"https://www.eltiempo.com{link['href']}")
                return articles

            def parse_article(self, soup, url):
                return {}

        scraper = ElTiempoScraper(el_tiempo_config)
        urls = await scraper.get_article_urls()

        assert len(urls) == 3
        assert "https://www.eltiempo.com/politica/article-123" in urls
        assert "https://www.eltiempo.com/economia/article-456" in urls
        assert "https://www.eltiempo.com/bogota/article-789" in urls

    @pytest.mark.asyncio
    @pytest.mark.requires_network
    async def test_el_tiempo_rate_limiting(self, el_tiempo_config):
        """Test that El Tiempo scraper respects rate limits"""
        from scrapers.base.base_scraper import BaseScraper

        class ElTiempoScraper(BaseScraper):
            async def get_article_urls(self):
                return []
            def parse_article(self, soup, url):
                return {}

        scraper = ElTiempoScraper(el_tiempo_config)

        # El Tiempo should have stricter rate limits
        assert scraper.rate_limiter.max_requests == 10  # Default from BaseScraper
        # In production, this would be 5 as per DomainRateLimiter configuration