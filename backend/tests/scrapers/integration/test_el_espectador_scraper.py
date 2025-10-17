"""
Integration tests for El Espectador scraper
"""
import pytest
from unittest.mock import Mock, patch
from aioresponses import aioresponses
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestElEspectadorScraper:
    """Test suite for El Espectador news scraper"""

    @pytest.fixture
    def el_espectador_config(self):
        """El Espectador configuration"""
        return {
            "name": "El Espectador",
            "url": "https://www.elespectador.com",
            "category": "national_media",
            "scrape_interval": 30
        }

    @pytest.fixture
    def sample_el_espectador_homepage(self):
        """Sample El Espectador homepage HTML"""
        return """
        <html>
        <body>
            <div class="Layout-Flex">
                <article class="Card">
                    <h2 class="Card-Title">
                        <a href="/politica/congreso-aprueba-reforma-tributaria-ARTICLE123">
                            Congreso aprueba reforma tributaria
                        </a>
                    </h2>
                    <p class="Card-Summary">La reforma incluye cambios significativos...</p>
                </article>
                <article class="Card">
                    <h2 class="Card-Title">
                        <a href="/economia/desempleo-baja-al-9-por-ciento-ARTICLE456">
                            Desempleo baja al 9% en Colombia
                        </a>
                    </h2>
                    <p class="Card-Summary">DANE reporta mejora en indicadores laborales...</p>
                </article>
            </div>
        </body>
        </html>
        """

    @pytest.fixture
    def sample_el_espectador_article(self):
        """Sample El Espectador article HTML"""
        return """
        <html>
        <head>
            <title>Congreso aprueba reforma tributaria | EL ESPECTADOR</title>
            <meta property="og:title" content="Congreso aprueba reforma tributaria">
            <meta property="og:description" content="La reforma incluye cambios significativos en el sistema impositivo">
            <meta name="author" content="María González">
        </head>
        <body>
            <article class="Article">
                <header class="Article-Header">
                    <h1 class="Article-Title">Congreso aprueba reforma tributaria</h1>
                    <div class="Article-Author">
                        <span>Por María González</span>
                    </div>
                    <time class="Article-Date">17 Oct 2025 - 2:30 PM</time>
                </header>
                <div class="Article-Content">
                    <p class="Article-Lead">
                        El Congreso de la República aprobó en último debate la reforma tributaria
                        que busca aumentar el recaudo en 25 billones de pesos.
                    </p>
                    <p>La votación final tuvo lugar en la plenaria del Senado con 85 votos a favor
                    y 15 en contra. La reforma incluye cambios en el impuesto de renta para
                    personas naturales y jurídicas.</p>
                    <p>El Ministro de Hacienda celebró la aprobación, destacando que estos recursos
                    serán fundamentales para financiar programas sociales y de infraestructura.</p>
                </div>
                <div class="Article-Tags">
                    <a class="Tag">Reforma Tributaria</a>
                    <a class="Tag">Congreso</a>
                    <a class="Tag">Economía</a>
                </div>
            </article>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_el_espectador_article_extraction(self, el_espectador_config, sample_el_espectador_article):
        """Test extraction of article content from El Espectador"""
        from scrapers.base.base_scraper import BaseScraper

        class ElEspectadorScraper(BaseScraper):
            async def get_article_urls(self):
                return ["https://www.elespectador.com/politica/congreso-aprueba-reforma-tributaria-ARTICLE123"]

            def parse_article(self, soup, url):
                title = soup.find("h1", class_="Article-Title")
                content_div = soup.find("div", class_="Article-Content")
                author_span = soup.find("div", class_="Article-Author")

                paragraphs = content_div.find_all("p") if content_div else []
                content = " ".join([p.text for p in paragraphs])

                author = ""
                if author_span:
                    author_text = author_span.find("span")
                    if author_text:
                        author = author_text.text.replace("Por ", "")

                return {
                    "title": title.text if title else "",
                    "content": content,
                    "author": author,
                    "url": url
                }

        scraper = ElEspectadorScraper(el_espectador_config)

        # Parse the sample article
        soup = scraper.parse_html(sample_el_espectador_article)
        article_data = scraper.parse_article(soup, "https://www.elespectador.com/politica/congreso-aprueba-reforma-tributaria-ARTICLE123")

        assert article_data["title"] == "Congreso aprueba reforma tributaria"
        assert "25 billones de pesos" in article_data["content"]
        assert article_data["author"] == "María González"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_el_espectador_homepage_parsing(self, el_espectador_config, sample_el_espectador_homepage):
        """Test parsing of El Espectador homepage for article URLs"""
        from scrapers.base.base_scraper import BaseScraper

        class ElEspectadorScraper(BaseScraper):
            async def get_article_urls(self):
                html = sample_el_espectador_homepage
                soup = self.parse_html(html)

                articles = []
                for card in soup.find_all("article", class_="Card"):
                    link = card.find("a")
                    if link and link.get("href"):
                        articles.append(f"https://www.elespectador.com{link['href']}")
                return articles

            def parse_article(self, soup, url):
                return {}

        scraper = ElEspectadorScraper(el_espectador_config)
        urls = await scraper.get_article_urls()

        assert len(urls) == 2
        assert "https://www.elespectador.com/politica/congreso-aprueba-reforma-tributaria-ARTICLE123" in urls
        assert "https://www.elespectador.com/economia/desempleo-baja-al-9-por-ciento-ARTICLE456" in urls

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_el_espectador_metadata_extraction(self, el_espectador_config, sample_el_espectador_article):
        """Test metadata extraction from El Espectador articles"""
        from scrapers.base.base_scraper import BaseScraper

        scraper = BaseScraper(el_espectador_config)
        soup = scraper.parse_html(sample_el_espectador_article)
        metadata = scraper.extract_metadata(soup)

        assert metadata["og_title"] == "Congreso aprueba reforma tributaria"
        assert metadata["og_description"] == "La reforma incluye cambios significativos en el sistema impositivo"

        # Check author from meta tags
        author_meta = soup.find("meta", attrs={"name": "author"})
        assert author_meta.get("content") == "María González"