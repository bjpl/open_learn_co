"""
Smart base scraper with rate limiting, retries, and caching
"""

import time
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import yaml
from dataclasses import dataclass
import logging
from functools import wraps
import redis

logger = logging.getLogger(__name__)


@dataclass
class ScrapedDocument:
    """Standard format for all scraped content"""
    source: str
    source_type: str
    url: str
    title: str
    content: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    scraped_at: datetime = None
    language: str = "es"
    difficulty_level: Optional[str] = None
    region: Optional[str] = None
    categories: List[str] = None

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
        if self.categories is None:
            self.categories = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'source': self.source,
            'source_type': self.source_type,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'metadata': self.metadata,
            'scraped_at': self.scraped_at.isoformat(),
            'language': self.language,
            'difficulty_level': self.difficulty_level,
            'region': self.region,
            'categories': self.categories
        }


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate: str):
        """
        Initialize rate limiter
        Args:
            rate: Rate string like "10/minute" or "100/hour"
        """
        parts = rate.split('/')
        self.max_requests = int(parts[0])

        if parts[1] == 'second':
            self.period = 1
        elif parts[1] == 'minute':
            self.period = 60
        elif parts[1] == 'hour':
            self.period = 3600
        else:
            self.period = 60  # Default to minute

        self.tokens = self.max_requests
        self.last_update = time.time()

    def acquire(self) -> bool:
        """Acquire a token for making a request"""
        now = time.time()
        elapsed = now - self.last_update

        # Replenish tokens
        tokens_to_add = elapsed * (self.max_requests / self.period)
        self.tokens = min(self.max_requests, self.tokens + tokens_to_add)
        self.last_update = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True

        # Calculate wait time
        wait_time = (1 - self.tokens) * (self.period / self.max_requests)
        logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
        time.sleep(wait_time)
        self.tokens = 0
        return True


class SmartScraper(ABC):
    """
    Enhanced base scraper with all the bells and whistles
    """

    def __init__(self, source_config: Dict = None):
        """Initialize smart scraper with configuration"""
        self.config = source_config or {}
        self.source_name = self.config.get('name', 'Unknown')
        self.base_url = self.config.get('url', '')
        self.rate_limiter = None

        # Set up rate limiting
        if 'rate_limit' in self.config:
            self.rate_limiter = RateLimiter(self.config['rate_limit'])

        # Create resilient session
        self.session = self._create_session()

        # Setup caching (optional)
        try:
            self.cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.cache.ping()
            self.cache_enabled = True
        except:
            self.cache_enabled = False
            logger.info(f"Redis not available, caching disabled for {self.source_name}")

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        return session

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return f"scraper:{self.source_name}:{hashlib.md5(url.encode()).hexdigest()}"

    def _get_cached(self, url: str) -> Optional[str]:
        """Get cached content if available"""
        if not self.cache_enabled:
            return None

        try:
            cache_key = self._get_cache_key(url)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {url}")
                return cached
        except Exception as e:
            logger.error(f"Cache error: {e}")

        return None

    def _set_cache(self, url: str, content: str, ttl: int = 3600):
        """Cache content with TTL"""
        if not self.cache_enabled:
            return

        try:
            cache_key = self._get_cache_key(url)
            self.cache.setex(cache_key, ttl, content)
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def fetch_page(self, url: str, use_cache: bool = True) -> Optional[str]:
        """
        Fetch a page with rate limiting and caching
        """
        # Check cache first
        if use_cache:
            cached = self._get_cached(url)
            if cached:
                return cached

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire()

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Cache successful response
            if use_cache:
                self._set_cache(url, response.text)

            return response.text

        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html, 'html.parser')

    @abstractmethod
    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from homepage - must be implemented by subclass"""
        pass

    @abstractmethod
    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from article - must be implemented by subclass"""
        pass

    def scrape_homepage(self) -> List[str]:
        """Scrape homepage for article URLs"""
        html = self.fetch_page(self.base_url)
        if not html:
            logger.error(f"Failed to fetch homepage for {self.source_name}")
            return []

        return self.extract_article_urls(html)

    def scrape_article(self, url: str) -> Optional[ScrapedDocument]:
        """Scrape a single article"""
        html = self.fetch_page(url)
        if not html:
            return None

        return self.extract_article_content(html, url)

    def scrape_batch(self, limit: int = 10) -> List[ScrapedDocument]:
        """
        Scrape multiple articles from source
        """
        logger.info(f"Starting batch scrape for {self.source_name}")

        # Get article URLs
        article_urls = self.scrape_homepage()[:limit]
        logger.info(f"Found {len(article_urls)} articles to scrape")

        # Scrape each article
        documents = []
        for url in article_urls:
            doc = self.scrape_article(url)
            if doc:
                documents.append(doc)
                logger.debug(f"Scraped: {doc.title}")

        logger.info(f"Successfully scraped {len(documents)} documents from {self.source_name}")
        return documents

    def validate_document(self, doc: ScrapedDocument) -> bool:
        """Validate scraped document has required fields"""
        if not doc.title or not doc.content:
            return False
        if len(doc.content) < 100:  # Minimum content length
            return False
        return True