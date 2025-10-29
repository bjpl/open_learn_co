"""
Test script for El Espectador scraper
Validates JSON-LD extraction and HTML fallback methods
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from scrapers.sources.media.el_espectador import ElEspectadorScraper
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_article_extraction():
    """Test extraction from a real article"""
    scraper = ElEspectadorScraper()

    # Test URL - recent politics article
    test_url = "https://www.elespectador.com/politica/registrador-penagos-insto-a-bajar-el-tono-de-confrontacion-politica-a-dos-anos-de-incendio-en-gamarra-noticias-hoy/"

    logger.info(f"Testing article extraction from: {test_url}")

    # Fetch the article page
    article_html = scraper.fetch_page(test_url)
    if not article_html:
        logger.error("Failed to fetch article page")
        return False

    logger.info(f"Fetched article HTML: {len(article_html)} bytes")

    # Extract article content
    doc = scraper.extract_article_content(article_html, test_url)

    if not doc:
        logger.error("Failed to extract article content")
        return False

    # Validate extracted data
    logger.info("=" * 80)
    logger.info("ARTICLE EXTRACTION RESULTS")
    logger.info("=" * 80)
    logger.info(f"Title: {doc.title}")
    logger.info(f"Author: {doc.author}")
    logger.info(f"Published: {doc.published_date}")
    logger.info(f"Category: {doc.metadata.get('category')}")
    logger.info(f"Word Count: {doc.metadata.get('word_count')}")
    logger.info(f"Content Length: {len(doc.content)} characters")
    logger.info(f"Difficulty: {doc.difficulty_level}")
    logger.info(f"Language: {doc.language}")
    logger.info(f"Region: {doc.region}")
    logger.info(f"Extraction Method: {doc.metadata.get('extraction_method')}")
    logger.info(f"\nFirst 300 chars of content:\n{doc.content[:300]}...")

    # Check for Colombian entities
    entities = doc.metadata.get('entities', {})
    if entities:
        logger.info(f"\nExtracted Colombian Entities:")
        for entity_type, items in entities.items():
            logger.info(f"  {entity_type}: {', '.join(items)}")

    # Validation checks
    checks = {
        "Has title": bool(doc.title and len(doc.title) > 10),
        "Has content": bool(doc.content and len(doc.content) > 500),
        "Has author": bool(doc.author),
        "Has date": bool(doc.published_date),
        "Has category": bool(doc.metadata.get('category')),
        "Content is Spanish text": all(word in doc.content.lower() for word in ['el', 'la', 'de']),
        "Reasonable word count": doc.metadata.get('word_count', 0) > 50
    }

    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION CHECKS")
    logger.info("=" * 80)
    for check, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {check}")

    all_passed = all(checks.values())
    logger.info("=" * 80)
    logger.info(f"Overall Result: {'✓ ALL CHECKS PASSED' if all_passed else '✗ SOME CHECKS FAILED'}")
    logger.info("=" * 80)

    return all_passed


def test_url_extraction():
    """Test URL extraction from homepage"""
    scraper = ElEspectadorScraper()

    logger.info("Testing URL extraction from homepage")

    homepage_html = scraper.fetch_page(scraper.base_url)
    if not homepage_html:
        logger.error("Failed to fetch homepage")
        return False

    urls = scraper.extract_article_urls(homepage_html)

    logger.info("=" * 80)
    logger.info("URL EXTRACTION RESULTS")
    logger.info("=" * 80)
    logger.info(f"Total URLs found: {len(urls)}")

    if urls:
        logger.info(f"\nFirst 10 article URLs:")
        for i, url in enumerate(urls[:10], 1):
            logger.info(f"  {i}. {url}")

    # Validation
    checks = {
        "Found URLs": len(urls) > 0,
        "URLs are valid": all(url.startswith('https://www.elespectador.com/') for url in urls),
        "URLs contain section": any(section in url for url in urls[:5] for section in ['/politica/', '/economia/', '/justicia/'])
    }

    logger.info("\nValidation Checks:")
    for check, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {check}")

    return all(checks.values())


def test_multiple_articles():
    """Test extraction from multiple articles"""
    scraper = ElEspectadorScraper()

    logger.info("Testing extraction from multiple articles")

    # Get some article URLs
    homepage_html = scraper.fetch_page(scraper.base_url)
    if not homepage_html:
        logger.error("Failed to fetch homepage")
        return False

    urls = scraper.extract_article_urls(homepage_html)

    if not urls:
        logger.error("No URLs found")
        return False

    # Test first 3 articles
    test_urls = urls[:3]
    results = []

    logger.info("=" * 80)
    logger.info(f"TESTING {len(test_urls)} ARTICLES")
    logger.info("=" * 80)

    for i, url in enumerate(test_urls, 1):
        logger.info(f"\nArticle {i}/{len(test_urls)}: {url}")

        article_html = scraper.fetch_page(url)
        if not article_html:
            logger.warning(f"  ✗ Failed to fetch")
            results.append(False)
            continue

        doc = scraper.extract_article_content(article_html, url)
        if not doc:
            logger.warning(f"  ✗ Failed to extract content")
            results.append(False)
            continue

        logger.info(f"  ✓ Title: {doc.title[:60]}...")
        logger.info(f"  ✓ Author: {doc.author}")
        logger.info(f"  ✓ Content: {len(doc.content)} chars, {doc.metadata.get('word_count')} words")
        logger.info(f"  ✓ Method: {doc.metadata.get('extraction_method')}")
        results.append(True)

    success_rate = sum(results) / len(results) * 100 if results else 0
    logger.info("\n" + "=" * 80)
    logger.info(f"Success Rate: {success_rate:.1f}% ({sum(results)}/{len(results)} articles)")
    logger.info("=" * 80)

    return success_rate >= 66.7  # At least 2/3 should succeed


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("EL ESPECTADOR SCRAPER TEST SUITE")
    print("=" * 80 + "\n")

    tests = [
        ("Article Extraction", test_article_extraction),
        ("URL Extraction", test_url_extraction),
        ("Multiple Articles", test_multiple_articles)
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{'=' * 80}")
        print(f"Running: {test_name}")
        print("=" * 80)
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test failed with exception: {e}", exc_info=True)
            results[test_name] = False

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())
    print("=" * 80)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 80 + "\n")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
