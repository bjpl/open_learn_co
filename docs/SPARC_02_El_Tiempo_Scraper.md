# SPARC Design: El Tiempo News Scraper

## S - Specification

### Purpose
Implement a specialized scraper for El Tiempo, Colombia's largest newspaper, to extract news articles for intelligence analysis and language learning.

### Requirements
- Extract articles from multiple sections (política, economía, justicia, deportes)
- Capture article metadata (author, date, category, tags)
- Handle dynamic content loading (JavaScript rendered pages)
- Extract Colombian-specific entities and terms
- Preserve article structure for language learning
- Handle paywall detection

### Data to Extract
- Article title and subtitle
- Full article text
- Author information
- Publication/update timestamps
- Category and tags
- Related articles
- Image captions
- Reader comments (if valuable)

## P - Pseudocode

```
ElTiempoScraper(BaseScraper):

    SECTIONS = [
        'politica', 'economia', 'justicia',
        'bogota', 'colombia', 'internacional'
    ]

    GET_ARTICLE_URLS():
        urls = []
        for section in SECTIONS:
            section_url = f"{base_url}/{section}"
            html = fetch_page(section_url)
            urls.extend(extract_article_links(html))
        return deduplicate(urls)

    PARSE_ARTICLE(soup, url):
        article = {}

        # Extract components
        article['title'] = extract_title(soup)
        article['subtitle'] = extract_subtitle(soup)
        article['author'] = extract_author(soup)
        article['content'] = extract_content(soup)
        article['published_date'] = extract_date(soup)
        article['category'] = extract_category(url)
        article['tags'] = extract_tags(soup)

        # Colombian context
        article['entities'] = extract_colombian_entities(content)
        article['difficulty_score'] = calculate_difficulty(content)

        return article

    EXTRACT_COLOMBIAN_ENTITIES(text):
        entities = []
        # Look for Colombian-specific patterns
        # Government institutions (MinDefensa, FARC, ELN)
        # Cities and departments
        # Political figures
        # Economic indicators (peso, UVR, etc.)
        return entities
```

## A - Architecture

### Integration Points
- Inherits from `BaseScraper`
- Uses `RateLimiter` for polite crawling
- Outputs to `ScrapedContent` model
- Feeds into NLP pipeline

### El Tiempo Specific Patterns
```python
# CSS Selectors
SELECTORS = {
    'title': 'h1.titulo',
    'subtitle': 'h2.sumario',
    'content': 'div.articulo-contenido',
    'author': 'div.autor-nombre',
    'date': 'span.fecha',
    'tags': 'div.tags a'
}
```

## R - Refinement

### Challenges & Solutions
1. **Paywall Detection**: Check for paywall indicators, mark articles
2. **Dynamic Content**: Use Selenium for JavaScript-heavy pages
3. **Rate Limiting**: Respect robots.txt, implement exponential backoff
4. **Content Quality**: Validate minimum content length

### Performance Optimizations
- Cache section pages for 5 minutes
- Batch process articles
- Skip already scraped content (check hash)

## C - Code Implementation

1. Implement ElTiempoScraper class
2. Add CSS selectors for content extraction
3. Create Colombian entity patterns
4. Add difficulty scoring algorithm
5. Test with real El Tiempo articles