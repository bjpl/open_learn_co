# Colombian News Scrapers Guide

This guide covers how to use and extend the 15+ news scrapers that collect content from Colombian media sources for intelligence gathering and language learning.

## Overview

The platform includes scrapers for major Colombian news sources:

### National Media
- **El Tiempo** - Colombia's largest newspaper
- **El Espectador** - Major national daily
- **Semana** - Weekly news magazine
- **La República** - Business newspaper
- **Portafolio** - Economic newspaper

### Radio and Digital
- **La FM** - Radio news content
- **Blu Radio** - Radio journalism
- **RCN Radio** - National radio network

### Regional Media
- **El Colombiano** (Antioquia)
- **El País** (Valle del Cauca)
- **El Heraldo** (Atlántico)
- **El Universal** (Bolívar)
- **Vanguardia** (Santander)
- **La Opinión** (Norte de Santander)

### Specialized Sources
- **Dinero** - Business magazine
- **La Silla Vacía** - Political analysis
- **Razón Pública** - Academic analysis
- **Colombia Check** - Fact checking

## Quick Start

### 1. Initialize a Scraper

```python
from backend.scrapers.sources.media.el_tiempo import ElTiempoScraper

config = {
    'base_url': 'https://eltiempo.com',
    'rate_limit': 5,  # Requests per minute
    'timeout': 30,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Platform Education Bot)'
    }
}

scraper = ElTiempoScraper(config)
```

### 2. Scrape Articles

```python
# Get article URLs from sections
urls = await scraper.get_article_urls()

# Scrape specific articles
articles = []
for url in urls[:10]:  # First 10 articles
    article = await scraper.scrape_article(url)
    if article:
        articles.append(article)

# Batch scraping
batch_articles = scraper.scrape_batch(limit=20)
```

## Scraper Architecture

### Base Scraper Class

All scrapers inherit from `BaseScraper`:

```python
from backend.scrapers.base.base_scraper import BaseScraper

class CustomScraper(BaseScraper):
    def __init__(self, source_config):
        super().__init__(source_config)
        self.setup_selectors()

    def setup_selectors(self):
        self.selectors = {
            'article_links': 'a.article-link',
            'title': 'h1.article-title',
            'content': 'div.article-content',
            'author': '.author-name',
            'date': 'time.publish-date'
        }

    async def get_article_urls(self):
        # Implementation for finding article URLs
        pass

    def parse_article(self, soup, url):
        # Implementation for parsing article content
        pass
```

### Smart Scraper

For unknown sites, use the AI-powered `SmartScraper`:

```python
from backend.scrapers.base.smart_scraper import SmartScraper

smart_scraper = SmartScraper({
    'base_url': 'https://unknown-news-site.com'
})

# Automatically detect content structure
article = await smart_scraper.scrape_article_smart(url)
```

## Detailed Scraper Usage

### El Tiempo Scraper

**Features**:
- Multi-section scraping (política, economía, justicia, etc.)
- Colombian entity extraction
- Difficulty scoring for language learning
- Paywall detection

```python
from backend.scrapers.sources.media.el_tiempo import ElTiempoScraper

scraper = ElTiempoScraper({
    'base_url': 'https://eltiempo.com',
    'rate_limit': 5
})

# Get economic news
economic_articles = await scraper.scrape_section('economia')

# Extract Colombian entities
for article in economic_articles:
    entities = article['colombian_entities']
    print(f"Institutions: {entities.get('institutions', [])}")
    print(f"Locations: {entities.get('locations', [])}")
    print(f"Political figures: {entities.get('political_figures', [])}")
```

**Article Structure**:
```json
{
  "title": "Colombia's Economy Shows Growth",
  "subtitle": "Economic indicators point to positive trends",
  "content": "La economía colombiana mostró signos...",
  "author": "María García",
  "published_date": "2024-01-15T10:00:00Z",
  "category": "economia",
  "tags": ["economía", "PIB", "DANE"],
  "url": "https://eltiempo.com/economia/article",
  "source": "El Tiempo",
  "colombian_entities": {
    "institutions": ["DANE", "Banco de la República"],
    "locations": ["Bogotá", "Colombia"],
    "economic_terms": ["PIB", "inflación"]
  },
  "difficulty_score": 3.2,
  "word_count": 456,
  "is_paywall": false
}
```

### El Espectador Scraper

**Features**:
- Clean content extraction
- Multimedia handling
- Opinion piece detection

```python
from backend.scrapers.sources.media.el_espectador import ElEspectadorScraper

scraper = ElEspectadorScraper({
    'base_url': 'https://elespectador.com'
})

# Scrape latest articles
articles = scraper.scrape_batch(limit=15)

# Filter by content type
news_articles = [a for a in articles if a['type'] == 'news']
opinion_pieces = [a for a in articles if a['type'] == 'opinion']
```

### Regional Scrapers

**El Colombiano (Antioquia)**:
```python
from backend.scrapers.sources.media.el_colombiano import ElColombianoScraper

scraper = ElColombianoScraper({
    'base_url': 'https://elcolombiano.com',
    'region': 'Antioquia'
})

# Get regional news
regional_news = await scraper.get_regional_content()
```

**Configuration for Regional Scrapers**:
```yaml
regional_scrapers:
  el_colombiano:
    region: "Antioquia"
    focus_cities: ["Medellín", "Bello", "Envigado"]
    local_topics: ["metro", "paisa", "antioquia"]

  el_pais:
    region: "Valle del Cauca"
    focus_cities: ["Cali", "Palmira", "Buenaventura"]
    local_topics: ["vallecaucano", "caleño"]
```

### Specialized Scrapers

**La Silla Vacía (Political Analysis)**:
```python
from backend.scrapers.sources.media.la_silla_vacia import LaSillaVaciaScraper

scraper = LaSillaVaciaScraper({
    'base_url': 'https://lasillavacia.com'
})

# Get political analysis articles
analysis = await scraper.get_political_analysis()

# Extract political figures and relationships
for article in analysis:
    political_network = article['political_network']
    print(f"Key figures: {political_network['figures']}")
    print(f"Relationships: {political_network['connections']}")
```

**Colombia Check (Fact Checking)**:
```python
from backend.scrapers.sources.media.colombia_check import ColombiaCheckScraper

scraper = ColombiaCheckScraper({
    'base_url': 'https://colombiacheck.com'
})

# Get fact-check articles
fact_checks = await scraper.get_fact_checks()

for check in fact_checks:
    print(f"Claim: {check['claim']}")
    print(f"Verdict: {check['verdict']}")  # True, False, Misleading, etc.
    print(f"Evidence: {check['evidence_summary']}")
```

## Content Processing

### Language Learning Features

**Difficulty Scoring**:
```python
def calculate_difficulty(text):
    """
    Calculate reading difficulty for Spanish learners
    Scale: 1.0 (beginner) to 5.0 (expert)
    """
    # Factors considered:
    # - Average sentence length
    # - Vocabulary complexity
    # - Technical terms
    # - Subjunctive usage
    # - Regional expressions
```

**Vocabulary Extraction**:
```python
def extract_vocabulary(article):
    """Extract educational vocabulary from articles"""
    return {
        'beginner': ['economía', 'gobierno', 'país'],
        'intermediate': ['crecimiento', 'inversión', 'desarrollo'],
        'advanced': ['macroeconómico', 'inflacionario', 'monetario'],
        'colombianisms': ['guayabo', 'parcero', 'chimba'],
        'formal_terms': ['procuraduría', 'contraloría', 'veeduría']
    }
```

### Colombian Entity Recognition

**Institution Detection**:
```python
institution_patterns = [
    r'\b(DANE|Banco de la República|Fiscalía)\b',
    r'\b(Procuraduría|Contraloría|Defensoría)\b',
    r'\b(MinDefensa|MinEducación|MinSalud)\b',
    r'\b(FARC|ELN|Clan del Golfo)\b'
]
```

**Geographic Recognition**:
```python
location_patterns = [
    r'\b(Bogotá|Medellín|Cali|Barranquilla)\b',
    r'\b(Cundinamarca|Antioquia|Valle del Cauca)\b',
    r'\b(Chocó|Nariño|Putumayo|Amazonas)\b'
]
```

**Political Figure Tracking**:
```python
political_patterns = [
    r'\b(Gustavo Petro|Francia Márquez)\b',
    r'\b(Álvaro Uribe|Juan Manuel Santos)\b',
    r'\b(Roy Barreras|Iván Cepeda)\b'
]
```

## Configuration

### Scraper Configuration File

`config/scrapers.yaml`:
```yaml
scrapers:
  el_tiempo:
    priority: "high"
    rate_limit: 5  # requests per minute
    sections: ["politica", "economia", "justicia", "bogota"]
    selectors:
      article: "article.article-container"
      title: "h1.titulo"
      content: "div.articulo-contenido"
      author: ".autor-nombre"
      date: ".fecha"

  el_espectador:
    priority: "high"
    rate_limit: 5
    sections: ["politica", "economia", "judicial"]
    selectors:
      article: "article.Article"
      title: "h1.Article-Title"
      content: "div.Article-Content"

  la_republica:
    priority: "medium"
    rate_limit: 3
    focus: "business"
    business_indicators:
      - "Dow Jones"
      - "Colcap"
      - "TRM"
```

### Environment Variables

```bash
# Rate limiting
SCRAPER_RATE_LIMIT=5  # requests per minute
SCRAPER_TIMEOUT=30    # seconds

# User agents
USER_AGENT_ROTATION=true
USER_AGENT_POOL="Mozilla/5.0 (compatible; EducationBot)"

# Storage
SCRAPED_CONTENT_PATH=/data/scraped
CONTENT_RETENTION_DAYS=30

# Language processing
ENABLE_ENTITY_EXTRACTION=true
ENABLE_DIFFICULTY_SCORING=true
SPANISH_NLP_MODEL=es_core_news_sm
```

## Rate Limiting and Ethics

### Respectful Scraping

```python
class RespectfulScraper:
    def __init__(self, config):
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.get('rate_limit', 5)
        )
        self.respect_robots_txt = True
        self.user_agent = "Educational Research Bot"

    async def fetch_page(self, url):
        # Check robots.txt
        if not await self.is_allowed(url):
            return None

        # Rate limiting
        await self.rate_limiter.acquire()

        # Fetch with proper headers
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8'
        }

        return await self.session.get(url, headers=headers)
```

### Best Practices

1. **Respect robots.txt**
2. **Use reasonable rate limits**
3. **Identify your bot properly**
4. **Don't overload servers**
5. **Cache responses appropriately**
6. **Handle errors gracefully**

## Error Handling

### Common Issues and Solutions

**Network Errors**:
```python
async def robust_fetch(self, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self.fetch_page(url)
        except aiohttp.ClientError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url}: {e}")
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

**Content Changes**:
```python
def adaptive_parsing(self, soup, url):
    """Try multiple parsing strategies"""
    strategies = [
        self.parse_with_selectors,
        self.parse_with_heuristics,
        self.parse_with_ai
    ]

    for strategy in strategies:
        try:
            result = strategy(soup, url)
            if self.validate_article(result):
                return result
        except Exception as e:
            logger.warning(f"Strategy failed for {url}: {e}")

    return None
```

**Anti-bot Measures**:
```python
class AntiDetectionScraper:
    def __init__(self):
        self.session_pool = SessionPool(size=5)
        self.proxy_rotator = ProxyRotator()
        self.user_agent_rotator = UserAgentRotator()

    async def fetch_with_rotation(self, url):
        session = await self.session_pool.get_session()
        proxy = await self.proxy_rotator.get_proxy()
        user_agent = self.user_agent_rotator.get_user_agent()

        return await session.get(url, proxy=proxy, headers={
            'User-Agent': user_agent
        })
```

## Testing Scrapers

### Unit Tests

```python
import pytest
from backend.scrapers.sources.media.el_tiempo import ElTiempoScraper

@pytest.mark.asyncio
async def test_el_tiempo_article_parsing():
    scraper = ElTiempoScraper({'base_url': 'https://test.eltiempo.com'})

    sample_html = """
    <article class="article-container">
        <h1 class="titulo">Test Article</h1>
        <div class="articulo-contenido">
            <p>Test content here.</p>
        </div>
    </article>
    """

    soup = BeautifulSoup(sample_html, 'html.parser')
    article = scraper.parse_article(soup, 'https://test.com/article')

    assert article['title'] == 'Test Article'
    assert 'Test content' in article['content']
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_scraper_pipeline():
    """Test complete scraping pipeline"""
    scraper = ElTiempoScraper(test_config)

    # Mock HTTP responses
    with aioresponses() as m:
        m.get('https://eltiempo.com/politica', body=section_html)
        m.get('https://eltiempo.com/article/1', body=article_html)

        urls = await scraper.get_article_urls()
        assert len(urls) > 0

        articles = await scraper.scrape_articles(urls[:5])
        assert len(articles) > 0

        for article in articles:
            assert_valid_article_structure(article)
```

## Adding New Scrapers

### Step 1: Create Scraper Class

```python
from backend.scrapers.base.base_scraper import BaseScraper

class NewSourceScraper(BaseScraper):
    def __init__(self, source_config):
        super().__init__(source_config)
        self.selectors = {
            'article_links': 'a.story-link',
            'title': 'h1.story-title',
            'content': 'div.story-body'
        }

    async def get_article_urls(self):
        """Get article URLs from the source"""
        # Implementation here
        pass

    def parse_article(self, soup, url):
        """Parse individual article"""
        # Implementation here
        pass
```

### Step 2: Add to Source Manager

```python
# In source_manager.py
scraper_map = {
    'el_tiempo': 'backend.scrapers.sources.media.el_tiempo.ElTiempoScraper',
    'new_source': 'backend.scrapers.sources.media.new_source.NewSourceScraper'
}
```

### Step 3: Update Configuration

```yaml
# In config/sources.yaml
media:
  national:
    new_source:
      name: "New Source"
      url: "https://newsource.com"
      type: "news"
      priority: "medium"
      scraping_interval: 60
      selectors:
        article: "article.news-item"
        title: "h1.headline"
        content: "div.body"
```

### Step 4: Add Tests

```python
class TestNewSourceScraper:
    @pytest.fixture
    def scraper(self):
        return NewSourceScraper({'base_url': 'https://test.newsource.com'})

    @pytest.mark.asyncio
    async def test_article_parsing(self, scraper):
        # Test implementation
        pass
```

## Monitoring and Analytics

### Scraping Metrics

```python
class ScrapingMetrics:
    def __init__(self):
        self.articles_scraped = 0
        self.success_rate = 0.0
        self.avg_response_time = 0.0
        self.errors_by_type = {}

    def record_success(self, response_time):
        self.articles_scraped += 1
        self.update_response_time(response_time)

    def record_error(self, error_type):
        self.errors_by_type[error_type] = \
            self.errors_by_type.get(error_type, 0) + 1
```

### Content Quality Metrics

```python
def assess_content_quality(article):
    """Assess the quality of scraped content"""
    quality_score = 0

    # Completeness
    if article.get('title') and article.get('content'):
        quality_score += 30

    # Content length
    if len(article.get('content', '')) > 200:
        quality_score += 20

    # Metadata presence
    if article.get('author') and article.get('published_date'):
        quality_score += 20

    # Colombian relevance
    if has_colombian_entities(article['content']):
        quality_score += 30

    return quality_score
```

### Dashboard Integration

```python
async def get_scraping_dashboard():
    """Get dashboard data for all scrapers"""
    dashboard = {
        'total_articles_today': 0,
        'active_scrapers': 0,
        'success_rates': {},
        'content_categories': {},
        'language_levels': {},
        'trending_topics': []
    }

    for scraper_name, scraper in active_scrapers.items():
        metrics = scraper.get_metrics()
        dashboard['success_rates'][scraper_name] = metrics['success_rate']

    return dashboard
```

## Performance Optimization

### Concurrent Scraping

```python
async def scrape_multiple_sources():
    """Scrape from multiple sources concurrently"""
    scrapers = [
        ElTiempoScraper(config),
        ElEspectadorScraper(config),
        SemanaScraper(config)
    ]

    tasks = [scraper.scrape_batch(limit=10) for scraper in scrapers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return process_results(results)
```

### Caching Strategies

```python
class CachedScraper:
    def __init__(self, scraper, cache_ttl=3600):
        self.scraper = scraper
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl)

    async def scrape_article(self, url):
        cache_key = f"article:{hash(url)}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        article = await self.scraper.scrape_article(url)
        self.cache[cache_key] = article
        return article
```

## Troubleshooting

### Common Problems

1. **Selector Changes**: Websites update their HTML structure
   - Solution: Use multiple selector strategies
   - Monitor for parsing failures
   - Implement adaptive parsing

2. **Rate Limiting**: Getting blocked by websites
   - Solution: Reduce scraping frequency
   - Use proxy rotation
   - Implement backoff strategies

3. **Content Quality**: Low-quality or incomplete articles
   - Solution: Improve content validation
   - Add quality scoring
   - Filter out low-quality content

4. **Memory Issues**: High memory usage with large content
   - Solution: Process articles in batches
   - Implement streaming parsing
   - Clear caches regularly

### Debug Mode

```python
scraper = ElTiempoScraper({
    'debug': True,
    'save_html': True,  # Save HTML for debugging
    'verbose_logging': True
})

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

For additional support, check the troubleshooting section in the main documentation or contact the development team.