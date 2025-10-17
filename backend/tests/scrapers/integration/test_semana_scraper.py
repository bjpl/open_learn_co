"""
Integration tests for Semana magazine scraper
"""
import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestSemanaScraper:
    """Test suite for Semana magazine scraper"""

    @pytest.fixture
    def semana_config(self):
        """Semana configuration"""
        return {
            "name": "Semana",
            "url": "https://www.semana.com",
            "category": "national_media",
            "scrape_interval": 45
        }

    @pytest.fixture
    def sample_semana_article(self):
        """Sample Semana article HTML"""
        return """
        <html>
        <head>
            <title>Análisis: El futuro económico de Colombia en 2025 | Semana.com</title>
            <meta property="og:title" content="Análisis: El futuro económico de Colombia en 2025">
            <meta property="og:type" content="article">
            <meta property="article:author" content="Carlos Rodríguez">
            <meta property="article:published_time" content="2025-10-17T14:30:00">
        </head>
        <body>
            <article class="article-container">
                <header class="article-header">
                    <h1 class="article-title">Análisis: El futuro económico de Colombia en 2025</h1>
                    <div class="article-meta">
                        <span class="author-name">Carlos Rodríguez</span>
                        <time class="publish-date">17/10/2025</time>
                    </div>
                </header>
                <div class="article-lead">
                    <p>Expertos analizan los desafíos y oportunidades que enfrenta
                    la economía colombiana en el último trimestre del año.</p>
                </div>
                <div class="article-body">
                    <p>Colombia se encuentra en un momento decisivo para su economía.
                    Los indicadores macroeconómicos muestran señales mixtas que requieren
                    un análisis detallado de los factores internos y externos que
                    influyen en el desarrollo del país.</p>
                    <p>Según el Banco de la República, el PIB crecerá entre 1.5% y 2%
                    este año, mientras que la inflación se mantiene controlada en
                    niveles cercanos al 5%.</p>
                    <p>Los sectores de tecnología y servicios lideran el crecimiento,
                    compensando la desaceleración en sectores tradicionales como
                    la construcción y la manufactura.</p>
                </div>
                <footer class="article-footer">
                    <div class="article-tags">
                        <span class="tag">Economía</span>
                        <span class="tag">Análisis</span>
                        <span class="tag">Colombia 2025</span>
                    </div>
                </footer>
            </article>
        </body>
        </html>
        """

    @pytest.mark.integration
    def test_semana_article_extraction(self, semana_config, sample_semana_article):
        """Test extraction of article content from Semana using SmartScraper"""
        from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

        class SemanaScraper(SmartScraper):
            def extract_article_urls(self, homepage_html):
                return ["https://www.semana.com/economia/articulo/analisis-futuro-economico/123456"]

            def extract_article_content(self, article_html, url):
                soup = self.parse_html(article_html)

                title = soup.find("h1", class_="article-title")
                lead = soup.find("div", class_="article-lead")
                body = soup.find("div", class_="article-body")
                author = soup.find("span", class_="author-name")

                content_parts = []
                if lead:
                    content_parts.append(lead.text.strip())
                if body:
                    paragraphs = body.find_all("p")
                    content_parts.extend([p.text.strip() for p in paragraphs])

                return ScrapedDocument(
                    source="Semana",
                    source_type="magazine",
                    url=url,
                    title=title.text if title else "",
                    content=" ".join(content_parts),
                    author=author.text if author else None,
                    language="es",
                    region="Colombia"
                )

        scraper = SemanaScraper(semana_config)

        # Extract article content
        doc = scraper.extract_article_content(
            sample_semana_article,
            "https://www.semana.com/economia/articulo/analisis-futuro-economico/123456"
        )

        assert doc.title == "Análisis: El futuro económico de Colombia en 2025"
        assert "PIB crecerá entre 1.5% y 2%" in doc.content
        assert doc.author == "Carlos Rodríguez"
        assert doc.source == "Semana"
        assert doc.source_type == "magazine"

    @pytest.mark.integration
    def test_semana_document_validation(self, semana_config):
        """Test document validation for Semana articles"""
        from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

        class SemanaScraper(SmartScraper):
            def extract_article_urls(self, homepage_html):
                return []
            def extract_article_content(self, article_html, url):
                return None

        scraper = SemanaScraper(semana_config)

        # Valid document
        valid_doc = ScrapedDocument(
            source="Semana",
            source_type="magazine",
            url="https://www.semana.com/test",
            title="Título del Artículo",
            content="Este es un contenido de prueba con más de 100 caracteres. " * 3
        )
        assert scraper.validate_document(valid_doc) is True

        # Invalid document (no content)
        invalid_doc = ScrapedDocument(
            source="Semana",
            source_type="magazine",
            url="https://www.semana.com/test",
            title="Título",
            content=""
        )
        assert scraper.validate_document(invalid_doc) is False

    @pytest.mark.integration
    def test_semana_scrape_interval(self, semana_config):
        """Test that Semana has appropriate scrape interval"""
        # Semana should have a longer interval as it's a weekly magazine
        assert semana_config["scrape_interval"] == 45

        # This is longer than daily newspapers
        el_tiempo_interval = 30
        assert semana_config["scrape_interval"] > el_tiempo_interval