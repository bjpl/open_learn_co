"""
Debug script to understand Portafolio HTML structure
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from scrapers.sources.media.portafolio import PortafolioScraper
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_portafolio():
    scraper = PortafolioScraper()
    test_url = "https://www.portafolio.co/economia/regiones/chez-migu-aterriza-en-bogota-con-su-propuesta-de-gastronomia-francesa-643216"

    logger.info("Fetching article...")
    html = scraper.fetch_page(test_url)

    if not html:
        logger.error("Failed to fetch")
        return

    soup = BeautifulSoup(html, 'html.parser')

    logger.info("\n=== TITLE SEARCH ===")
    for selector in ['h1[itemprop="headline"]', 'h1.title', 'h1']:
        elem = soup.select_one(selector)
        if elem:
            logger.info(f"✓ Found with '{selector}': {elem.get_text()[:100]}")
            break
    else:
        logger.warning("No title found with any selector")

    logger.info("\n=== CONTENT SEARCH ===")
    for selector in ['div[itemprop="articleBody"]', '.article-body', '.story-content', 'article', 'main']:
        elem = soup.select_one(selector)
        if elem:
            paragraphs = elem.find_all('p')
            logger.info(f"✓ Found with '{selector}': {len(paragraphs)} paragraphs")
            if paragraphs:
                logger.info(f"  First paragraph: {paragraphs[0].get_text()[:150]}")
            break
    else:
        logger.warning("No content found with any selector")

    logger.info("\n=== ALL PARAGRAPHS IN BODY ===")
    all_paragraphs = soup.find_all('p')
    logger.info(f"Total <p> tags in document: {len(all_paragraphs)}")
    for i, p in enumerate(all_paragraphs[:10]):
        text = p.get_text().strip()
        if len(text) > 30:
            logger.info(f"  P{i+1} ({len(text)} chars): {text[:100]}...")

    logger.info("\n=== AUTHOR SEARCH ===")
    for selector in ['span[itemprop="author"]', 'a[itemprop="author"]', '.author-name']:
        elem = soup.select_one(selector)
        if elem:
            logger.info(f"✓ Found with '{selector}': {elem.get_text()}")
            break

    logger.info("\n=== DATE SEARCH ===")
    for selector in ['time[itemprop="datePublished"]', 'time[datetime]', 'time']:
        elem = soup.select_one(selector)
        if elem:
            logger.info(f"✓ Found with '{selector}': {elem.get_text()} | datetime={elem.get('datetime')}")
            break

    logger.info("\n=== STRUCTURED DATA ===")
    json_ld = soup.find('script', type='application/ld+json')
    if json_ld:
        import json
        try:
            data = json.loads(json_ld.string)
            logger.info("✓ Found JSON-LD structured data:")
            if isinstance(data, dict):
                logger.info(f"  @type: {data.get('@type')}")
                logger.info(f"  headline: {data.get('headline', 'N/A')[:100]}")
                logger.info(f"  author: {data.get('author', 'N/A')}")
                logger.info(f"  datePublished: {data.get('datePublished', 'N/A')}")
                logger.info(f"  articleBody present: {'articleBody' in data}")
                if 'articleBody' in data:
                    logger.info(f"  articleBody length: {len(data['articleBody'])} chars")
        except Exception as e:
            logger.error(f"Error parsing JSON-LD: {e}")


if __name__ == "__main__":
    debug_portafolio()
