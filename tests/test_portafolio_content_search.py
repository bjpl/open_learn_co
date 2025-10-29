"""
Find where the actual article content is located
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from scrapers.sources.media.portafolio import PortafolioScraper
from bs4 import BeautifulSoup


def find_content():
    scraper = PortafolioScraper()
    test_url = "https://www.portafolio.co/economia/regiones/chez-migu-aterriza-en-bogota-con-su-propuesta-de-gastronomia-francesa-643216"

    html = scraper.fetch_page(test_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Look for article content in common containers
    print("=== SEARCHING FOR ARTICLE CONTENT ===\n")

    # Check all divs with meaningful text
    print("1. Checking for divs with substantial text:")
    all_divs = soup.find_all('div')
    content_candidates = []

    for div in all_divs:
        # Get text but exclude scripts and styles
        for script in div.find_all(['script', 'style']):
            script.decompose()

        text = div.get_text(strip=True)
        if 300 < len(text) < 10000:  # Reasonable article length
            # Get class names
            classes = ' '.join(div.get('class', []))
            content_candidates.append((len(text), classes, text[:200]))

    # Sort by length
    content_candidates.sort(reverse=True)

    print(f"Found {len(content_candidates)} potential content containers\n")

    for i, (length, classes, preview) in enumerate(content_candidates[:5]):
        print(f"Candidate {i+1}:")
        print(f"  Length: {length} chars")
        print(f"  Classes: {classes}")
        print(f"  Preview: {preview}...")
        print()

    # Check for common content class patterns
    print("\n2. Checking specific patterns:")
    patterns = [
        'articulo', 'article', 'content', 'body', 'texto', 'noticia',
        'post', 'entry', 'main', 'story', 'detail'
    ]

    for pattern in patterns:
        # Try different attribute combinations
        for attr in ['class', 'id']:
            elems = soup.find_all(lambda tag: tag.get(attr) and pattern in str(tag.get(attr)).lower())
            if elems:
                for elem in elems[:2]:
                    text = elem.get_text(strip=True)
                    if len(text) > 200:
                        print(f"  Found via {attr}*='{pattern}': {elem.name} ({len(text)} chars)")
                        print(f"    {attr}: {elem.get(attr)}")
                        print(f"    Preview: {text[:150]}...")
                        print()


if __name__ == "__main__":
    find_content()
