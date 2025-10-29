"""
Test script to verify Portafolio scraper fixes
Tests real article extraction with the updated scraper
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from scrapers.sources.media.portafolio import PortafolioScraper
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_portafolio_scraper():
    """Test Portafolio scraper with real article"""
    logger.info("=" * 80)
    logger.info("Testing Portafolio Scraper")
    logger.info("=" * 80)

    # Initialize scraper
    scraper = PortafolioScraper()

    # Test article URL from Portafolio
    test_url = "https://www.portafolio.co/economia/regiones/chez-migu-aterriza-en-bogota-con-su-propuesta-de-gastronomia-francesa-643216"

    logger.info(f"\n1. Testing article extraction from: {test_url}")

    # Fetch the article
    article_html = scraper.fetch_page(test_url)

    if not article_html:
        logger.error("Failed to fetch article HTML")
        return False

    logger.info(f"✓ Successfully fetched article (HTML length: {len(article_html)} chars)")

    # Extract content
    document = scraper.extract_article_content(article_html, test_url)

    if not document:
        logger.error("Failed to extract article content")
        return False

    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("EXTRACTION RESULTS")
    logger.info("=" * 80)
    logger.info(f"Title: {document.title}")
    logger.info(f"Author: {document.author}")
    logger.info(f"Date: {document.published_date}")
    logger.info(f"Category: {document.metadata.get('category', 'N/A')}")
    logger.info(f"Content length: {len(document.content)} chars")
    logger.info(f"Word count: {document.metadata.get('word_count', 0)}")
    logger.info(f"Difficulty: {document.difficulty_level}")
    logger.info(f"\nContent preview (first 500 chars):")
    logger.info("-" * 80)
    logger.info(document.content[:500] + "...")
    logger.info("-" * 80)

    # Validate extraction
    issues = []

    if not document.title or len(document.title) < 10:
        issues.append("❌ Title too short or missing")
    else:
        logger.info("✓ Title extracted successfully")

    if not document.content or len(document.content) < 250:
        issues.append("❌ Content too short or missing")
    else:
        logger.info("✓ Content extracted successfully")

    if not document.author or document.author == "Unknown":
        issues.append("⚠️  Author not found (using default)")
    else:
        logger.info("✓ Author extracted successfully")

    if not document.published_date:
        issues.append("⚠️  Date not found")
    else:
        logger.info("✓ Date extracted successfully")

    # Test homepage URL extraction
    logger.info("\n" + "=" * 80)
    logger.info("2. Testing homepage URL extraction")
    logger.info("=" * 80)

    homepage_html = scraper.fetch_page(scraper.base_url)
    if homepage_html:
        urls = scraper.extract_article_urls(homepage_html)
        logger.info(f"✓ Extracted {len(urls)} article URLs from homepage")
        if urls:
            logger.info("\nSample URLs:")
            for i, url in enumerate(urls[:5], 1):
                logger.info(f"  {i}. {url}")
    else:
        issues.append("❌ Failed to fetch homepage")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    if issues:
        logger.warning(f"Found {len(issues)} issues:")
        for issue in issues:
            logger.warning(f"  {issue}")
    else:
        logger.info("✓ All tests passed successfully!")

    logger.info("=" * 80)

    return len(issues) == 0


if __name__ == "__main__":
    success = test_portafolio_scraper()
    sys.exit(0 if success else 1)
