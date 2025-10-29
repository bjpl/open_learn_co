"""
Test script for El Tiempo scraper with JSON-LD extraction
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from scrapers.sources.media.el_tiempo import ElTiempoScraper


async def test_scraper():
    """Test El Tiempo scraper"""
    print("=" * 80)
    print("Testing El Tiempo Scraper with JSON-LD Extraction")
    print("=" * 80)

    # Initialize scraper
    config = {
        'name': 'El Tiempo',
        'url': 'https://www.eltiempo.com',
        'type': 'media',
        'category': 'news',
        'enabled': True
    }

    scraper = ElTiempoScraper(config)
    articles = []

    # Use async context manager to initialize session
    async with scraper:
        try:
            # Test 1: Get article URLs
            print("\n[TEST 1] Fetching article URLs...")
            urls = await scraper.get_article_urls()
            print(f"Found {len(urls)} article URLs")

            if urls:
                print("\nSample URLs:")
                for url in urls[:5]:
                    print(f"  - {url}")

            # Test 2: Scrape articles
            print("\n[TEST 2] Scraping articles...")
            articles = await scraper.scrape()

            print(f"\nTotal articles scraped: {len(articles)}")

            # Test 3: Analyze results
            print("\n[TEST 3] Analyzing scraped articles...")

            with_dates = 0
            without_dates = 0
            paywall_count = 0

            for article in articles:
                # Count extraction methods (check logs would be ideal, but we'll infer)
                if article.published_date:
                    with_dates += 1
                else:
                    without_dates += 1

                if hasattr(article, 'is_paywall') and article.is_paywall:
                    paywall_count += 1

            print(f"\nArticles with dates: {with_dates}")
            print(f"Articles without dates: {without_dates}")
            print(f"Paywall articles: {paywall_count}")

            # Test 4: Display sample articles
            print("\n[TEST 4] Sample article details:")
            print("-" * 80)

            for i, article in enumerate(articles[:3], 1):
                print(f"\nArticle {i}:")
                print(f"  Title: {getattr(article, 'title', 'N/A')[:80]}")
                print(f"  Author: {getattr(article, 'author', 'N/A')}")
                print(f"  Date: {getattr(article, 'published_date', 'N/A')}")
                print(f"  Category: {getattr(article, 'category', 'N/A')}")

                tags = getattr(article, 'tags', [])
                if tags:
                    if isinstance(tags, str):
                        print(f"  Tags: {tags}")
                    else:
                        print(f"  Tags: {', '.join([str(t) for t in tags[:5]])}")

                print(f"  Word count: {getattr(article, 'word_count', 0)}")
                print(f"  Difficulty: {getattr(article, 'difficulty_score', 0)}")

                content = getattr(article, 'content', '')
                print(f"  Content preview: {content[:150]}...")
                print(f"  Paywall: {getattr(article, 'is_paywall', False)}")

                # Check for image URL in extra_metadata
                extra_meta = getattr(article, 'extra_metadata', {})
                if extra_meta and isinstance(extra_meta, dict):
                    image_url = extra_meta.get('image_url')
                    if image_url:
                        print(f"  Image: {image_url[:80]}")

                if hasattr(article, 'colombian_entities'):
                    entities = article.colombian_entities
                    if entities:
                        print(f"  Colombian entities:")
                        if isinstance(entities, str):
                            print(f"    {entities}")
                        elif isinstance(entities, dict):
                            for entity_type, values in entities.items():
                                vals_str = ', '.join([str(v) for v in values[:3]])
                                print(f"    {entity_type}: {vals_str}")

            # Test 5: Quality checks
            print("\n[TEST 5] Quality checks:")
            print("-" * 80)

            if articles:
                avg_word_count = sum(getattr(a, 'word_count', 0) for a in articles) / len(articles)
                avg_difficulty = sum(getattr(a, 'difficulty_score', 0) for a in articles) / len(articles)

                print(f"Average word count: {avg_word_count:.1f}")
                print(f"Average difficulty: {avg_difficulty:.1f}")

                articles_with_content = sum(1 for a in articles if len(getattr(a, 'content', '')) > 200)
                print(f"Articles with substantial content (>200 chars): {articles_with_content}/{len(articles)}")

                articles_with_authors = sum(1 for a in articles if getattr(a, 'author', None) and getattr(a, 'author', '') != 'El Tiempo')
                print(f"Articles with specific authors: {articles_with_authors}/{len(articles)}")

                articles_with_tags = sum(1 for a in articles if getattr(a, 'tags', None))
                print(f"Articles with tags: {articles_with_tags}/{len(articles)}")

            # Test 6: Success rate
            print("\n[TEST 6] Success rate:")
            print("-" * 80)

            success_rate = (len(articles) / len(urls) * 100) if urls else 0
            print(f"Extraction success rate: {success_rate:.1f}% ({len(articles)}/{len(urls)})")

            if articles:
                quality_articles = sum(1 for a in articles if
                                     getattr(a, 'content', None) and
                                     len(getattr(a, 'content', '')) > 200 and
                                     getattr(a, 'published_date', None))

                quality_rate = (quality_articles / len(articles) * 100)
                print(f"Quality article rate: {quality_rate:.1f}% ({quality_articles}/{len(articles)})")

            print("\n" + "=" * 80)
            print("TEST COMPLETE")
            print("=" * 80)

        except Exception as e:
            print(f"\nError during testing: {str(e)}")
            import traceback
            traceback.print_exc()

    return articles


if __name__ == "__main__":
    articles = asyncio.run(test_scraper())
