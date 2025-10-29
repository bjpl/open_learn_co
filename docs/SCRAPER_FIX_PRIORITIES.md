# Scraper Fix Priorities - Quick Reference for Agents

## Critical Issues Requiring Immediate Attention

### 1. EL TIEMPO - Date Parsing Bug (CRITICAL)
**File:** `backend/scrapers/sources/media/el_tiempo.py`
**Lines:** 219-240 (_parse_date method)
**Issue:** Method returns `datetime.utcnow()` on line 238 as fallback - ALL articles get current date
**Fix Required:**
- Remove hardcoded `datetime.utcnow()` fallback (line 240)
- Implement proper Spanish date parsing
- Handle Colombian timezone (UTC-5)
- Test with actual date formats from site

**Related Code:**
```python
# CURRENT BROKEN CODE (line 238-240)
return datetime.utcnow().isoformat()  # WRONG: Returns current date always

# NEEDS TO:
# 1. Try datetime attribute from element
# 2. Try regex patterns against date text
# 3. Parse Spanish month names
# 4. Return None or raise exception if can't parse (don't default to now)
```

---

### 2. ALL SCRAPERS - Content Container Extraction (CRITICAL)
**Affected Files:**
- `backend/scrapers/sources/media/el_tiempo.py` (line 39: `.articulo-contenido`)
- `backend/scrapers/sources/media/el_espectador.py` (line 46: `.Article-content`)
- `scrapers/semana_scraper.py` (line 47: `.article-body`)
- `scrapers/portafolio_scraper.py` (line 47: `.article-body`)

**Issue:** CSS class selectors appear outdated - need verification against live sites
**Fix Required:**
1. Test selectors against actual website HTML
2. Update class names to match current structure
3. Add schema.org `itemprop="articleBody"` as reliable fallback
4. Consider regex patterns for more flexibility

**Testing Commands:**
```bash
# For each site, fetch an article and inspect:
curl https://www.eltiempo.com/[article-url] | grep -i "content\|article-body\|story"
curl https://www.elespectador.com/[article-url] | grep -i "content\|article-body"
curl https://www.semana.com/[article-url] | grep -i "content\|article-body"
curl https://www.portafolio.co/[article-url] | grep -i "content\|article-body"
```

---

### 3. ALL SCRAPERS - Article Link Discovery (CRITICAL)
**Affected Files:**
- `backend/scrapers/sources/media/el_espectador.py` (line 43: `.Card-link, .CardHome-link`)
- `scrapers/semana_scraper.py` (line 44: `.card-link, .article-link`)
- `scrapers/portafolio_scraper.py` (line 44: `.story-card a, .article-link`)

**Issue:** Component class names may have changed with site redesigns
**Fix Required:**
1. Inspect homepage HTML for article link structure
2. Identify current card/link container classes
3. Test against multiple article discovery methods:
   - Direct class selectors
   - Href regex patterns
   - Data attributes if used
4. Update URL filtering to match actual article paths

**Best Practice:** Use href regex patterns (like El Espectador root version) for flexibility

---

## High Priority Fixes

### 4. Title Selector Fallback Pattern
**Issue:** Bare `h1` fallback may capture page headers
**All Files Affected - Update priority:**
- `backend/scrapers/sources/media/el_tiempo.py` (line 37)
- `backend/scrapers/sources/media/el_espectador.py` (line 44)
- `scrapers/semana_scraper.py` (line 45)
- `scrapers/portafolio_scraper.py` (line 45)

**Better Approach:**
```python
# Instead of: 'title': 'h1.article-title, h1.title, h1'
# Use fallback chain:
title_selectors = [
    'h1.article-title',      # Most specific
    'h1[class*="title"]',    # Any class containing "title"
    ('meta', 'og:title'),    # Meta tag (most reliable)
    'h1'                     # Bare h1 as absolute last resort
]
```

---

### 5. Paywall Detection Refinement
**Affected Files:**
- `backend/scrapers/sources/media/el_tiempo.py` (line 201: 200 char threshold)
- `scrapers/portafolio_scraper.py` (line 116: keyword detection)
- `scrapers/semana_scraper.py` (line 318: 300 char threshold)

**Issue:** Content length < 200 chars triggers false positive for paywalled content
**Fix:**
- Remove length-based heuristic
- Use only keyword detection (suscríbete, contenido exclusivo, etc.)
- Consider paywall metadata if available
- Allow short articles to be scraped anyway

---

## Medium Priority Fixes

### 6. Date Parsing - Add Multiple Format Support
**El Espectador Root Version** has best implementation (lines 251-356)
**Recommend copying approach to:**
- `backend/scrapers/sources/media/el_tiempo.py`
- `backend/scrapers/sources/media/el_espectador.py`

**Current Good Pattern (Semana):**
```python
patterns = [
    r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',  # "15 de enero de 2024"
    r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',          # "enero 15, 2024"
    r'(\d{1,2})/(\d{1,2})/(\d{4})'             # "15/01/2024"
]
```

---

### 7. Author Extraction - Cleanup Common Prefixes
**All Files:** Add prefix removal similar to root El Espectador (line 208)
```python
author_text = re.sub(r'^(Por:?\s*|Redacción\s*|@)', '', author_text, flags=re.IGNORECASE)
```

---

### 8. Section List Maintenance
**Files with hardcoded sections:**
- `backend/scrapers/sources/media/el_tiempo.py` (lines 23-32)
- `backend/scrapers/sources/media/el_espectador.py` (lines 28-39)
- `scrapers/semana_scraper.py` (lines 30-40)
- `scrapers/portafolio_scraper.py` (lines 31-40)

**Recommendation:** Either:
1. Auto-detect sections from site navigation
2. Document expected sections with links for verification
3. Implement fallback article discovery from homepage

---

## File-by-File Priority Matrix

### EL TIEMPO (backend/scrapers/sources/media/el_tiempo.py)
| Issue | Line | Priority | Type |
|-------|------|----------|------|
| Date parsing returns current date | 238 | CRITICAL | Bug |
| Content container selector outdated | 39 | CRITICAL | Verification |
| Title fallback to bare h1 | 37 | HIGH | Pattern |
| Paywall detection threshold | 213 | HIGH | Tuning |
| URL article pattern may miss articles | 108 | MEDIUM | Verification |

### EL ESPECTADOR - BACKEND (backend/scrapers/sources/media/el_espectador.py)
| Issue | Line | Priority | Type |
|-------|------|----------|------|
| Article link classes outdated | 43 | CRITICAL | Verification |
| Content container class outdated | 46 | CRITICAL | Verification |
| Title fallback to bare h1 | 44 | HIGH | Pattern |
| All class-based selectors fragile | Multiple | HIGH | Architecture |

### SEMANA (scrapers/semana_scraper.py)
| Issue | Line | Priority | Type |
|-------|------|----------|------|
| Article link classes outdated | 44 | CRITICAL | Verification |
| Content container classes outdated | 47 | CRITICAL | Verification |
| Promotional content filter over-aggressive | 318 | HIGH | Tuning |
| Content minimum 300 chars may filter short articles | 403 | HIGH | Tuning |

### PORTAFOLIO (scrapers/portafolio_scraper.py)
| Issue | Line | Priority | Type |
|-------|------|----------|------|
| Article link selectors questionable | 44 | CRITICAL | Verification |
| Content container classes outdated | 47 | CRITICAL | Verification |
| Paywall detection doesn't stop processing | 317 | MEDIUM | Tuning |

### EL ESPECTADOR - ROOT (scrapers/el_espectador_scraper.py)
| Issue | Line | Priority | Type |
|-------|------|----------|------|
| Section list may be incomplete | 145 | MEDIUM | Verification |
| Bare h1 fallback acceptable but verify | 179 | MEDIUM | Pattern |
| Content pattern very broad | 222 | MEDIUM | Refinement |

---

## Testing Commands for Verification

```bash
# Test El Tiempo
python -c "from backend.scrapers.sources.media.el_tiempo import ElTiempoScraper; s = ElTiempoScraper({'name': 'test', 'url': 'https://www.eltiempo.com'}); print(s.selectors)"

# Test El Espectador
python -c "from scrapers.el_espectador_scraper import ElEspectadorScraper; s = ElEspectadorScraper(); print(s.sections)"

# Test Semana
python -c "from scrapers.semana_scraper import SemanaScraper; s = SemanaScraper(); print(s.selectors)"

# Test Portafolio
python -c "from scrapers.portafolio_scraper import PortafolioScraper; s = PortafolioScraper(); print(s.sections)"
```

---

## Testing Methodology

For each scraper fix:

1. **Fetch Sample Article**
   - Get real article URL from site
   - Save HTML to local file for offline testing

2. **Verify Selectors**
   ```python
   from bs4 import BeautifulSoup
   with open('sample_article.html', 'r') as f:
       soup = BeautifulSoup(f, 'html.parser')
       title = soup.select_one(selector)
       print(f"Title found: {title is not None}")
       if title:
           print(f"Title text: {title.get_text()[:50]}...")
   ```

3. **Compare Multiple Articles**
   - Test 3-5 articles from different sections
   - Verify consistency of selector patterns
   - Document any variations found

4. **Validate Extraction Quality**
   - Verify title is actually article title (not nav, breadcrumb, etc.)
   - Verify content contains full article body
   - Verify author name is correct
   - Verify date is publication date (not current date)

---

## Known Working Patterns (Use as Reference)

### Best Selector Approach (El Espectador Root)
```python
# Uses regex patterns for flexibility
article_links = soup.find_all("a", href=re.compile(r"/(noticias|politica|economia|judicial|colombia|deportes|entretenimiento)/"))

# Uses selector fallback chain with meta tags
title_selectors = [
    ("h1", {"class": re.compile(r"title|titulo|headline", re.I)}),
    ("h1", {}),
    ("meta", {"property": "og:title"}),
]
```

### Best Date Parsing (Semana, Portafolio)
```python
# Try HTML5 time element first
time_elem = soup.select_one('time')
if time_elem and time_elem.get('datetime'):
    return datetime.fromisoformat(time_elem.get('datetime'))

# Try meta tag
meta_date = soup.find("meta", attrs={"property": "article:published_time"})
if meta_date:
    return datetime.fromisoformat(meta_date.get("content"))

# Fall back to Spanish date parsing
# NOT to current datetime!
```

### Best Content Extraction (Portafolio, Semana)
```python
# Get container
content_elem = soup.select_one('.article-body, .story-content, .body-text')

# Extract paragraphs with minimum length filter
paragraphs = content_elem.find_all('p')
for p in paragraphs:
    text = clean_text(p.get_text())
    if text and len(text) > 30:  # Minimum length
        content_parts.append(text)

# Filter out promotional content
if not is_promotional(text):
    content_parts.append(text)
```

---

## Summary of What Agents Need to Do

1. **Inspect** - Use browser DevTools on live websites
2. **Update** - Modify selectors to match actual HTML
3. **Test** - Verify against 3-5 real articles
4. **Validate** - Ensure extracted content is correct and complete
5. **Document** - Note what selectors worked and why

**Success Criteria:**
- All four scraper files tested and updated
- Selectors verified against live sites
- 90%+ extraction success rate across test articles
- No critical bugs remaining
- Proper fallback chains implemented
- Test coverage documented
