# Semana Scraper Fix - October 28, 2025

## Problem
The Semana scraper was unable to extract article content from Semana.com. The CSS selectors were outdated and didn't match the current website structure, which uses Tailwind CSS utility classes.

## Analysis
- Website now uses modern Tailwind CSS framework with dynamic class names
- Old selectors like `.article-body`, `.story-content` no longer exist
- Website provides JSON-LD structured data with complete article content
- Found 4 JSON-LD scripts per page, including a NewsArticle type with full content

## Solution Implemented

### 1. Primary Method: JSON-LD Extraction
Added `_extract_json_ld()` method that:
- Parses JSON-LD structured data from `<script type="application/ld+json">` tags
- Extracts NewsArticle or Article types
- Gets headline, articleBody, author, datePublished directly from structured data
- More reliable than HTML parsing

### 2. Fallback Method: Updated HTML Parsing
Updated `_extract_from_html()` with:
- Generic selectors that work with current structure
- Uses `<h1>` for title (no class required)
- Uses `<article>` element for content container
- Extracts all `<p>` tags within article element
- Filters promotional content

### 3. Enhanced Error Handling
- Try JSON-LD first (most reliable)
- Fall back to HTML parsing if JSON-LD unavailable
- Better logging for debugging
- Metadata tracking for extraction method used

## Code Changes

### File: `backend/scrapers/sources/media/semana.py`

**Added:**
- `import json` at top of file
- `_extract_json_ld(soup)` - Extract JSON-LD NewsArticle data
- `_create_document_from_json_ld(data, url, soup)` - Create document from JSON-LD
- `_extract_from_html(soup, url)` - Updated HTML fallback method

**Modified:**
- `extract_article_content()` - Now tries JSON-LD first, then HTML fallback
- Added `extraction_method` to metadata for tracking

## Test Results

### URL Extraction
- **Status:** ✓ PASS
- **Result:** Found 287 article URLs from homepage

### JSON-LD Extraction
- **Status:** ✓ PASS
- **Method:** Successfully using JSON-LD structured data
- **Sample:** Extracted article with title, author, date, content

### Content Quality
- **Status:** ✓ PASS
- **Word Count:** 500+ words per article
- **Content Length:** 2000+ characters per article

### Metadata Extraction
- **Status:** ✓ PASS
- **Fields:** Title, Author, Date, Category, Difficulty all present

### Multiple Article Success Rate
- **Status:** ✓ PASS
- **Rate:** 90% success (9/10 articles)
- **Expected:** ≥80% threshold

## Integration Tests
All existing integration tests continue to pass:
- `test_semana_article_extraction` ✓
- `test_semana_document_validation` ✓
- `test_semana_scrape_interval` ✓

## Benefits

1. **Reliability:** JSON-LD is more stable than HTML scraping
2. **Robustness:** Fallback to HTML if JSON-LD unavailable
3. **Maintainability:** Less dependent on changing CSS classes
4. **Performance:** JSON-LD parsing is faster than complex HTML traversal
5. **Completeness:** Gets full article content including metadata

## Examples

### Extracted Article Sample
```
Title: Remezón en el Ministerio de Minas: piden renuncia...
Author: Redacción Economía
Date: 2025-10-27 17:44:38-05:00
Category: Economia
Word Count: 539
Difficulty: Avanzado
Method: json-ld
```

## Recommendations

1. **Monitor:** Track extraction_method in metrics to see JSON-LD vs HTML ratio
2. **Extend:** Apply JSON-LD extraction to other scrapers where available
3. **Update:** If success rate drops below 80%, investigate site changes
4. **Test:** Run periodic live tests to catch breaking changes early

## Technical Notes

- Semana.com uses proper semantic HTML with JSON-LD
- JSON-LD follows schema.org NewsArticle standard
- Site has 4 JSON-LD blocks: BreadcrumbList, NewsArticle, Organization, WebSite
- OpenGraph metadata available as secondary source
- HTML fallback uses generic tags (`<article>`, `<h1>`, `<p>`)

## File Location
- **Scraper:** `backend/scrapers/sources/media/semana.py`
- **Tests:** `backend/tests/scrapers/integration/test_semana_scraper.py`
