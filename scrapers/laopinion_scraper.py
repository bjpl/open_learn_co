"""
La Opinión scraper implementation
Leading newspaper from Cúcuta and Norte de Santander region
URL: https://www.laopinion.com.co
Difficulty: Medium - Regional focus with border news coverage
"""

import re
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LaOpinionScraper:
    """Scraper for La Opinión (laopinion.com.co)"""

    def __init__(self):
        self.name = "La Opinión"
        self.base_url = "https://www.laopinion.com.co"
        self.session = self._create_session()

        self.sections = [
            'cucuta',
            'norte-santander',
            'frontera',
            'colombia',
            'politica',
            'economia',
            'deportes',
            'cultura'
        ]

        # CSS selectors for La Opinión's structure
        self.selectors = {
            'article_links': 'article a, .article-link, .story-link, h2 a, h3 a',
            'title': 'h1.title, h1.article-title, h1',
            'subtitle': '.summary, .excerpt, .lead, .bajada',
            'content': '.article-content, .body-content, .story-text',
            'author': '.author, .byline, .firma',
            'date': 'time, .date, .publish-date',
            'category': '.category, '.section-name',
            'tags': '.tags a, .keywords a'
        }

        # Rate limiting - regional newspaper
        self.request_delay = 2.3  # seconds between requests
        self.last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })

        return session

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page with rate limiting and error handling"""
        self._rate_limit()

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup"""
        return BeautifulSoup(html, 'html.parser')

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        text = ' '.join(text.split())
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _is_article_url(self, url: str) -> bool:
        """Check if URL is a valid La Opinión article"""
        article_indicators = [
            '/cucuta/',
            '/norte-santander/',
            '/frontera/',
            '/colombia/',
            '/politica/',
            '/economia/',
            '/deportes/',
            '/cultura/'
        ]

        exclude_patterns = [
            '/autor/',
            '/tag/',
            '/especial/',
            '/galeria/',
            '/video/',
            '#',
            'mailto:',
            'javascript:',
            '.pdf',
            'twitter.com',
            'facebook.com'
        ]

        has_indicator = any(indicator in url.lower() for indicator in article_indicators)
        should_exclude = any(pattern in url.lower() for pattern in exclude_patterns)

        return has_indicator and not should_exclude

    def _get_article_urls(self, max_articles: int = 20) -> List[str]:
        """Extract article URLs from La Opinión homepage and sections"""
        urls = set()

        # Get articles from homepage
        logger.info(f"Fetching homepage: {self.base_url}")
        homepage_html = self._fetch_page(self.base_url)

        if homepage_html:
            soup = self._parse_html(homepage_html)
            article_links = soup.select(self.selectors['article_links'])

            for link in article_links:
                href = link.get('href', '')
                if href:
                    if href.startswith('/'):
                        href = self.base_url + href
                    if self._is_article_url(href):
                        urls.add(href)

        # Get articles from main sections
        for section in self.sections[:3]:  # Limit to 3 sections
            if len(urls) >= max_articles:
                break

            section_url = f"{self.base_url}/{section}"
            logger.info(f"Fetching section: {section}")
            section_html = self._fetch_page(section_url)

            if section_html:
                section_soup = self._parse_html(section_html)
                section_links = section_soup.select(self.selectors['article_links'])

                for link in section_links:
                    href = link.get('href', '')
                    if href:
                        if href.startswith('/'):
                            href = self.base_url + href
                        if self._is_article_url(href):
                            urls.add(href)

        return list(urls)[:max_articles]

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            '.author',
            '.byline',
            '.firma',
            '[rel="author"]'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                author_text = re.sub(r'^(Por:?\s*|Redacción\s*|@)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return author_text

        return "La Opinión"

    def _extract_date(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract publication date"""
        # Try time element first
        time_elem = soup.select_one('time')
        if time_elem and time_elem.get('datetime'):
            try:
                dt = datetime.fromisoformat(time_elem.get('datetime').replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except:
                pass

        # Try other date selectors
        date_selectors = ['.date', '.publish-date', '.fecha']
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = self._clean_text(date_elem.get_text())
                parsed_date = self._parse_spanish_date(date_text)
                if parsed_date:
                    return parsed_date.strftime('%Y-%m-%d')

        return datetime.now().strftime('%Y-%m-%d')

    def _parse_spanish_date(self, date_text: str) -> Optional[datetime]:
        """Parse Spanish date formats"""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        patterns = [
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if '/' in pattern:
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    else:
                        day, month_name, year = match.groups()
                        month = months.get(month_name.lower())
                        if month:
                            return datetime(int(year), month, int(day))
                except:
                    continue

        return None

    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        category_selectors = ['.category', '.section-name']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                return section.replace('-', ' ').title()

        return 'Regional'

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags"""
        tags = []
        tag_elements = soup.select(self.selectors['tags'])

        for tag_elem in tag_elements:
            tag_text = self._clean_text(tag_elem.get_text())
            if tag_text:
                tags.append(tag_text)

        return tags

    def _parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse a single article"""
        logger.info(f"Scraping article: {url}")

        html = self._fetch_page(url)
        if not html:
            return None

        soup = self._parse_html(html)

        try:
            # Extract title
            title_elem = soup.select_one(self.selectors['title'])
            if not title_elem:
                logger.warning(f"No title found for {url}")
                return None
            title = self._clean_text(title_elem.get_text())

            # Extract subtitle
            subtitle_elem = soup.select_one(self.selectors['subtitle'])
            subtitle = self._clean_text(subtitle_elem.get_text()) if subtitle_elem else ""

            # Extract content
            content_elem = soup.select_one(self.selectors['content'])
            if not content_elem:
                logger.warning(f"No content found for {url}")
                return None

            # Process content paragraphs
            content_parts = []
            if subtitle:
                content_parts.append(subtitle)

            paragraphs = content_elem.find_all('p')
            for p in paragraphs:
                text = self._clean_text(p.get_text())
                if text and len(text) > 30:
                    content_parts.append(text)

            content = ' '.join(content_parts)

            # Check content quality
            if len(content) < 200:
                logger.warning(f"Content too short for {url}")
                return None

            # Extract metadata
            author = self._extract_author(soup)
            published_date = self._extract_date(soup, url)
            category = self._extract_category(soup, url)
            tags = self._extract_tags(soup)

            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            return {
                'title': title,
                'subtitle': subtitle,
                'content': content,
                'author': author,
                'published_date': published_date,
                'category': category,
                'url': url,
                'tags': tags,
                'content_hash': content_hash,
                'source': self.name,
                'scraped_at': datetime.now().isoformat(),
                'word_count': len(content.split()),
                'difficulty': 'medium',
                'region': 'Norte de Santander',
                'specialization': 'border_news'
            }

        except Exception as e:
            logger.error(f"Error parsing article {url}: {str(e)}")
            return None

    def scrape(self, max_articles: int = 20) -> List[Dict[str, Any]]:
        """Main scraping method"""
        logger.info(f"Starting scrape for {self.name}")
        articles = []

        try:
            article_urls = self._get_article_urls(max_articles)
            logger.info(f"Found {len(article_urls)} article URLs")

            for url in article_urls:
                article_data = self._parse_article(url)
                if article_data:
                    articles.append(article_data)
                    logger.info(f"Successfully scraped: {article_data['title'][:60]}...")

                time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")

        logger.info(f"Completed scraping {self.name}: {len(articles)} articles")
        return articles

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


if __name__ == "__main__":
    with LaOpinionScraper() as scraper:
        articles = scraper.scrape(max_articles=5)

        print(f"\n{'='*80}")
        print(f"Scraped {len(articles)} articles from La Opinión")
        print(f"{'='*80}\n")

        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']}")
            print(f"   Author: {article['author']}")
            print(f"   Date: {article['published_date']}")
            print(f"   Category: {article['category']}")
            print()
