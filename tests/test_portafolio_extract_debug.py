"""
Debug exact extraction process
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from scrapers.sources.media.portafolio import PortafolioScraper
from bs4 import BeautifulSoup


def debug_extraction():
    scraper = PortafolioScraper()
    test_url = "https://www.portafolio.co/economia/regiones/chez-migu-aterriza-en-bogota-con-su-propuesta-de-gastronomia-francesa-643216"

    html = scraper.fetch_page(test_url)
    soup = BeautifulSoup(html, 'html.parser')

    print("=== CONTENT EXTRACTION DEBUG ===\n")

    # Try the content selector
    content_elem = soup.select_one('#articulocontenido')

    if content_elem:
        print(f"✓ Found #articulocontenido")
        print(f"  Raw text length: {len(content_elem.get_text())} chars")

        # Get all paragraphs
        paragraphs = content_elem.find_all('p')
        print(f"  Total <p> tags: {len(paragraphs)}")

        print("\n  Paragraph analysis:")
        for i, p in enumerate(paragraphs):
            # Check for scripts/styles
            has_script = p.find(['script', 'style', 'noscript'])

            text = scraper._clean_text(p.get_text())

            is_promo = scraper._is_promotional_content(text)
            is_nav = scraper._is_navigation_text(text)

            status = "✓ KEPT"
            reasons = []

            if has_script:
                status = "✗ SKIPPED"
                reasons.append("has_script")
            elif len(text) <= 30:
                status = "✗ SKIPPED"
                reasons.append(f"too_short({len(text)})")
            elif is_promo:
                status = "✗ SKIPPED"
                reasons.append("promotional")
            elif is_nav:
                status = "✗ SKIPPED"
                reasons.append("navigation")

            reason_str = f" [{', '.join(reasons)}]" if reasons else ""
            print(f"    P{i+1} {status}{reason_str}: {text[:80]}...")

        # Now try the actual extraction logic
        print("\n=== SIMULATING EXTRACTION ===")
        content_parts = []

        for p in paragraphs:
            if p.find(['script', 'style', 'noscript']):
                continue

            text = scraper._clean_text(p.get_text())

            if text and len(text) > 30:
                if not scraper._is_promotional_content(text) and not scraper._is_navigation_text(text):
                    content_parts.append(text)

        content = ' '.join(content_parts)
        print(f"\nFinal content length: {len(content)} chars")
        print(f"Content parts: {len(content_parts)}")
        print(f"\nFirst 300 chars of content:")
        print(content[:300])

    else:
        print("✗ #articulocontenido not found")


if __name__ == "__main__":
    debug_extraction()
