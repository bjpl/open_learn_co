"""
W Radio news scraper implementation
Caracol Radio's flagship news and opinion station
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
import requests
from time import sleep

logger = logging.getLogger(__name__)


class WRadioScraper:
    """Scraper for W Radio (wradio.com.co)"""

    def __init__(self, source_config: Dict = None):
        """Initialize W Radio scraper with configuration"""
        config = source_config or {
            'name': 'W Radio',
            'url': 'https://www.wradio.com.co',
            'rate_limit': '15/minute'
        }

        self.source_name = config.get('name', 'W Radio')
        self.base_url = config.get('url', 'https://www.wradio.com.co').rstrip('/')
        self.rate_limit_delay = 4  # 15 requests/minute = 4 seconds between requests

        self.sections = [
            'noticias',
            'colombia',
            'internacional',
            'politica',
            'economia',
            'deportes',
            'entretenimiento',
            'tecnologia'
        ]

        # CSS selectors for W Radio's structure (Fusion/Arc Publishing platform)
        self.selectors = {
            'article_links': 'article a, .story-card a, .card-link, h2 a, h3 a',
            'title': 'h1.headline, h1.story-headline, h1',
            'subtitle': '.subheadline, .lead-art-caption, .article-subtitle',
            'content': '.article-body, .story-body, .body-content, article p',
            'author': '.author-name, .by-author, .byline, .story-byline',
            'date': 'time, .story-date, .publish-date',
            'category': '.story-section, .section-name, .category',
            'tags': '.story-tags a, .tags a, .article-tags a',
            'audio': 'audio source, .audio-player, iframe[src*="audio"]'
        }

        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.wradio.com.co/',
            'DNT': '1'
        }

    def scrape(self, max_articles: int = 50) -> List[Dict[str, Any]]:
        """
        Main scraping method that fetches and parses W Radio articles

        Args:
            max_articles: Maximum number of articles to scrape

        Returns:
            List of scraped article dictionaries
        """
        logger.info(f"Starting W Radio scraper - target: {max_articles} articles")
        articles = []
        urls = self._get_article_urls(limit=max_articles)

        for idx, url in enumerate(urls, 1):
            try:
                logger.info(f"[{idx}/{len(urls)}] Scraping: {url}")
                article_data = self._scrape_article(url)

                if article_data:
                    articles.append(article_data)
                    logger.info(f"Successfully scraped: {article_data['title'][:60]}...")
                else:
                    logger.warning(f"Failed to extract data from: {url}")

                # Rate limiting
                if idx < len(urls):
                    sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                continue

        logger.info(f"W Radio scraping complete: {len(articles)} articles scraped")
        return articles

    def _get_article_urls(self, limit: int = 50) -> List[str]:
        """
        Extract article URLs from W Radio homepage and sections

        Args:
            limit: Maximum number of URLs to collect

        Returns:
            List of unique article URLs
        """
        urls = set()

        # Start with homepage
        try:
            logger.info(f"Fetching homepage: {self.base_url}")
            html = self._fetch_page(self.base_url)
            if html:
                urls.update(self._extract_urls_from_html(html))
        except Exception as e:
            logger.error(f"Error fetching homepage: {e}")

        # Fetch from sections if we need more
        for section in self.sections:
            if len(urls) >= limit:
                break

            try:
                section_url = f"{self.base_url}/{section}"
                logger.info(f"Fetching section: {section_url}")
                html = self._fetch_page(section_url)

                if html:
                    urls.update(self._extract_urls_from_html(html))

                sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"Error fetching section {section}: {e}")
                continue

        # Filter and limit URLs
        valid_urls = [url for url in urls if self._is_article_url(url)]
        logger.info(f"Found {len(valid_urls)} valid article URLs")

        return valid_urls[:limit]

    def _fetch_page(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Fetch HTML content from URL with error handling

        Args:
            url: Target URL
            timeout: Request timeout in seconds

        Returns:
            HTML content as string or None if failed
        """
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            return None

    def _extract_urls_from_html(self, html: str) -> set:
        """Extract article URLs from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        urls = set()

        # Find all article links
        for selector in self.selectors['article_links'].split(', '):
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if href:
                        # Handle relative URLs
                        if href.startswith('/'):
                            href = self.base_url + href
                        elif not href.startswith('http'):
                            continue

                        if self._is_article_url(href):
                            urls.add(href)
            except Exception as e:
                logger.debug(f"Error extracting links with selector {selector}: {e}")
                continue

        return urls

    def _is_article_url(self, url: str) -> bool:
        """
        Check if URL is a valid W Radio article

        Args:
            url: URL to validate

        Returns:
            True if URL appears to be an article
        """
        # Must be from wradio.com.co
        if 'wradio.com.co' not in url.lower():
            return False

        # Article indicators
        article_indicators = [
            '/noticias/',
            '/colombia/',
            '/internacional/',
            '/politica/',
            '/economia/',
            '/deportes/',
            '/entretenimiento/',
            '/tecnologia/',
            '/noticia/',
            '/articulo/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/programa/',
            '/emisora/',
            '/directorio/',
            '/vivo/',
            '/podcast/',
            '/audio-completo/',
            '/video/',
            '/galeria/',
            '/tag/',
            '/autor/',
            '/opinion/',
            '#',
            'mailto:',
            'javascript:',
            'twitter.com',
            'facebook.com',
            'instagram.com',
            'youtube.com',
            '.mp3',
            '.mp4',
            '.pdf',
            '.jpg',
            '.png'
        ]

        # Check indicators
        has_indicator = any(indicator in url.lower() for indicator in article_indicators)

        # Check exclusions
        should_exclude = any(pattern in url.lower() for pattern in exclude_patterns)

        # Check for article ID pattern (Arc Publishing uses numerical IDs)
        has_id = bool(re.search(r'/\d{4,}', url))

        return (has_indicator or has_id) and not should_exclude

    def _scrape_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape single article from W Radio

        Args:
            url: Article URL

        Returns:
            Dictionary with article data or None if failed
        """
        html = self._fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        try:
            # Extract title (required)
            title = self._extract_title(soup)
            if not title:
                logger.warning(f"No title found for {url}")
                return None

            # Extract content (required)
            content = self._extract_content(soup)
            if not content or len(content) < 150:
                logger.warning(f"Insufficient content for {url}")
                return None

            # Extract other fields
            author = self._extract_author(soup)
            published_date = self._extract_date(soup, url)
            category = self._extract_category(soup, url)
            audio_urls = self._extract_audio_urls(soup)

            # Build article data
            article_data = {
                'source': self.source_name,
                'source_type': 'radio',
                'url': url,
                'title': title,
                'content': content,
                'author': author,
                'published_date': published_date,
                'category': category,
                'word_count': len(content.split()),
                'has_audio': len(audio_urls) > 0,
                'audio_urls': audio_urls,
                'media_group': 'Caracol',
                'language': 'es',
                'region': 'Colombia',
                'scraped_at': datetime.utcnow().isoformat()
            }

            return article_data

        except Exception as e:
            logger.error(f"Error parsing article {url}: {str(e)}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        for selector in self.selectors['title'].split(', '):
            try:
                elem = soup.select_one(selector)
                if elem:
                    title = self._clean_text(elem.get_text())
                    if title and len(title) > 10:
                        return title
            except:
                continue

        # Fallback to meta tags
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return self._clean_text(og_title.get('content', ''))

        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content, filtering promotional text"""
        content_parts = []

        # Try subtitle/lead
        subtitle_elem = soup.select_one(self.selectors['subtitle'])
        if subtitle_elem:
            subtitle = self._clean_text(subtitle_elem.get_text())
            if subtitle and len(subtitle) > 20:
                content_parts.append(subtitle)

        # Extract main content
        content_elem = soup.select_one(self.selectors['content'])
        if content_elem:
            # Get all paragraphs
            paragraphs = content_elem.find_all('p')
            for p in paragraphs:
                text = self._clean_text(p.get_text())
                if text and len(text) > 20:
                    # Filter promotional content
                    if not self._is_promotional_content(text):
                        content_parts.append(text)
        else:
            # Fallback: get all paragraphs from article
            article_elem = soup.find('article')
            if article_elem:
                paragraphs = article_elem.find_all('p')
                for p in paragraphs:
                    text = self._clean_text(p.get_text())
                    if text and len(text) > 20:
                        if not self._is_promotional_content(text):
                            content_parts.append(text)

        if content_parts:
            return ' '.join(content_parts)

        return None

    def _is_promotional_content(self, text: str) -> bool:
        """Check if text is promotional/non-editorial content"""
        promo_indicators = [
            'escucha en vivo',
            'sintoniza',
            'frecuencia',
            'descarga la app',
            'suscríbete',
            'síguenos en',
            'escucha el programa',
            'transmisión en vivo',
            'podcast completo',
            'audio completo',
            'w radio colombia',
            'caracol radio',
            'en el aire',
            'pulsa aquí',
            'haz clic',
            'más información',
            'lee también',
            'te puede interesar'
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in promo_indicators)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        # Try author selectors
        for selector in self.selectors['author'].split(', '):
            try:
                elem = soup.select_one(selector)
                if elem:
                    author = self._clean_text(elem.get_text())
                    # Clean common prefixes
                    author = re.sub(r'^(Por:?\s*|Redacción\s*|@)', '', author, flags=re.IGNORECASE)
                    if author and len(author) > 2:
                        return author
            except:
                continue

        # Fallback to meta tags
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            return self._clean_text(author_meta.get('content', ''))

        return self.source_name

    def _extract_date(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract publication date in ISO format"""
        # Try time element with datetime attribute
        time_elem = soup.select_one('time')
        if time_elem and time_elem.get('datetime'):
            try:
                date_str = time_elem.get('datetime')
                # Parse and return ISO format
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.isoformat()
            except:
                pass

        # Try date selectors
        for selector in self.selectors['date'].split(', '):
            try:
                elem = soup.select_one(selector)
                if elem:
                    date_text = self._clean_text(elem.get_text())
                    parsed_date = self._parse_spanish_date(date_text)
                    if parsed_date:
                        return parsed_date.isoformat()
            except:
                continue

        # Try meta tags
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            try:
                dt = datetime.fromisoformat(date_meta.get('content', '').replace('Z', '+00:00'))
                return dt.isoformat()
            except:
                pass

        # Extract from URL pattern
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if date_match:
            year, month, day = date_match.groups()
            try:
                return datetime(int(year), int(month), int(day)).isoformat()
            except:
                pass

        # Fallback to current time
        return datetime.utcnow().isoformat()

    def _parse_spanish_date(self, date_text: str) -> Optional[datetime]:
        """Parse Spanish date formats"""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        patterns = [
            (r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', lambda m: datetime(
                int(m.group(3)),
                months.get(m.group(2).lower(), 1),
                int(m.group(1))
            )),
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: datetime(
                int(m.group(3)),
                int(m.group(2)),
                int(m.group(1))
            )),
            (r'(\d{4})-(\d{2})-(\d{2})', lambda m: datetime(
                int(m.group(1)),
                int(m.group(2)),
                int(m.group(3))
            )),
            (r'Hace\s+(\d+)\s+(hora|día|minuto)s?', lambda m: {
                'hora': datetime.utcnow() - timedelta(hours=int(m.group(1))),
                'día': datetime.utcnow() - timedelta(days=int(m.group(1))),
                'minuto': datetime.utcnow() - timedelta(minutes=int(m.group(1)))
            }.get(m.group(2), datetime.utcnow()))
        ]

        for pattern, parser in patterns:
            match = re.search(pattern, date_text, re.IGNORECASE)
            if match:
                try:
                    return parser(match)
                except:
                    continue

        return None

    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        # Try category selectors
        for selector in self.selectors['category'].split(', '):
            try:
                elem = soup.select_one(selector)
                if elem:
                    category = self._clean_text(elem.get_text())
                    if category and category.lower() not in ['inicio', 'home', 'w radio']:
                        return category
            except:
                continue

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                return section.replace('-', ' ').title()

        return 'Noticias'

    def _extract_audio_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract audio URLs from the page"""
        audio_urls = []

        # Look for audio elements
        audio_elements = soup.find_all('audio')
        for audio in audio_elements:
            src = audio.get('src')
            if src:
                audio_urls.append(src)

            # Check source children
            sources = audio.find_all('source')
            for source in sources:
                src = source.get('src')
                if src:
                    audio_urls.append(src)

        # Look for embedded audio players (iframes)
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if 'audio' in src.lower() or 'player' in src.lower():
                audio_urls.append(src)

        return list(set(audio_urls))  # Remove duplicates

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove extra whitespace
        text = ' '.join(text.split())
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()
