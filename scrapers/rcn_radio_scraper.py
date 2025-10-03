"""
RCN Radio news scraper for Colombia Intelligence platform
Scrapes news from https://www.rcnradio.com
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import hashlib
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RCNRadioScraper:
    """Scraper for RCN Radio news website"""

    def __init__(self):
        self.name = "RCN Radio"
        self.base_url = "https://www.rcnradio.com"
        self.category = "news"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.rate_limit_delay = 1.5  # Seconds between requests

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page with error handling and rate limiting"""
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                return None

        except requests.Timeout:
            logger.error(f"Timeout fetching {url}")
            return None
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup"""
        return BeautifulSoup(html, 'html.parser')

    def generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""

        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove common noise
        text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")

        return text.strip()

    def extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags from article"""
        tags = []

        # Try to find tags in meta keywords
        keywords_meta = soup.find("meta", attrs={"name": "keywords"})
        if keywords_meta and keywords_meta.get("content"):
            keywords = keywords_meta.get("content", "").split(",")
            tags.extend([k.strip() for k in keywords if k.strip()])

        # Try to find tags in article body
        tag_elements = soup.find_all("a", class_=re.compile("tag|etiqueta", re.I))
        for tag_elem in tag_elements:
            tag_text = self.clean_text(tag_elem.get_text())
            if tag_text and tag_text not in tags:
                tags.append(tag_text)

        return tags[:10]  # Limit to 10 tags

    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        metadata = {}

        # Open Graph tags
        og_tags = soup.find_all("meta", property=lambda x: x and x.startswith("og:"))
        for tag in og_tags:
            key = tag.get("property", "").replace("og:", "")
            metadata[f"og_{key}"] = tag.get("content", "")

        # Twitter Card tags
        twitter_tags = soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")})
        for tag in twitter_tags:
            key = tag.get("name", "").replace("twitter:", "")
            metadata[f"twitter_{key}"] = tag.get("content", "")

        # Standard meta tags
        description = soup.find("meta", attrs={"name": "description"})
        if description:
            metadata["description"] = description.get("content", "")

        # Publication date
        pub_date = soup.find("meta", attrs={"property": "article:published_time"})
        if pub_date:
            metadata["published_time"] = pub_date.get("content", "")

        # Author
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta:
            metadata["author"] = author_meta.get("content", "")

        return metadata

    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None

        try:
            # Try common date formats
            formats = [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M",
                "%Y-%m-%d",
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.isoformat()
                except ValueError:
                    continue

            return None
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {str(e)}")
            return None

    def get_article_urls(self, limit: int = 20) -> List[str]:
        """Get list of recent article URLs from homepage and sections"""
        article_urls = []

        # Sections to scrape
        sections = [
            "",  # Homepage
            "/colombia",
            "/bogota",
            "/politica",
            "/economia",
            "/internacional",
            "/deportes",
        ]

        for section in sections:
            url = f"{self.base_url}{section}"
            html = self.fetch_page(url)

            if not html:
                continue

            soup = self.parse_html(html)

            # Find article links - RCN Radio typically uses article tags
            articles = soup.find_all("article")
            for article in articles:
                link = article.find("a", href=True)
                if link:
                    href = link.get("href", "")

                    # Make absolute URL
                    if href.startswith("/"):
                        full_url = f"{self.base_url}{href}"
                    elif href.startswith("http"):
                        full_url = href
                    else:
                        continue

                    # Only add RCN Radio URLs
                    if "rcnradio.com" in full_url and full_url not in article_urls:
                        article_urls.append(full_url)

                        if len(article_urls) >= limit:
                            return article_urls

            # Also look for links with article patterns
            links = soup.find_all("a", href=re.compile(r"/(noticia|articulo|colombia|bogota|politica|economia)/"))
            for link in links:
                href = link.get("href", "")

                # Make absolute URL
                if href.startswith("/"):
                    full_url = f"{self.base_url}{href}"
                elif href.startswith("http"):
                    full_url = href
                else:
                    continue

                # Only add RCN Radio URLs
                if "rcnradio.com" in full_url and full_url not in article_urls:
                    article_urls.append(full_url)

                    if len(article_urls) >= limit:
                        return article_urls

        logger.info(f"Found {len(article_urls)} article URLs")
        return article_urls

    def parse_article(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse article content from BeautifulSoup object"""
        try:
            # Extract title
            title = None
            title_elem = soup.find("h1")
            if title_elem:
                title = self.clean_text(title_elem.get_text())

            if not title:
                # Try Open Graph title
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    title = og_title.get("content", "")

            if not title:
                logger.warning(f"No title found for {url}")
                return None

            # Extract content - try multiple selectors
            content = ""
            content_selectors = [
                {"name": "div", "class_": re.compile("article-content|article-body|entry-content|post-content", re.I)},
                {"name": "div", "itemprop": "articleBody"},
                {"name": "article"},
            ]

            for selector in content_selectors:
                content_elem = soup.find(**selector)
                if content_elem:
                    # Get all paragraphs
                    paragraphs = content_elem.find_all("p")
                    if paragraphs:
                        content = " ".join([self.clean_text(p.get_text()) for p in paragraphs])
                        break

            if not content or len(content) < 100:
                logger.warning(f"Insufficient content for {url}")
                return None

            # Extract author
            author = None
            author_selectors = [
                {"name": "span", "class_": re.compile("author|autor", re.I)},
                {"name": "a", "rel": "author"},
                {"itemprop": "author"},
            ]

            for selector in author_selectors:
                author_elem = soup.find(**selector)
                if author_elem:
                    author = self.clean_text(author_elem.get_text())
                    break

            if not author:
                # Try meta tag
                metadata = self.extract_metadata(soup)
                author = metadata.get("author", "RCN Radio")

            if not author:
                author = "RCN Radio"

            # Extract published date
            published_date = None
            date_selectors = [
                {"name": "time", "datetime": True},
                {"name": "span", "class_": re.compile("date|fecha", re.I)},
                {"itemprop": "datePublished"},
            ]

            for selector in date_selectors:
                date_elem = soup.find(**selector)
                if date_elem:
                    date_str = date_elem.get("datetime") or self.clean_text(date_elem.get_text())
                    published_date = self.parse_date(date_str)
                    if published_date:
                        break

            if not published_date:
                # Try meta tag
                pub_meta = soup.find("meta", property="article:published_time")
                if pub_meta:
                    published_date = self.parse_date(pub_meta.get("content", ""))

            if not published_date:
                published_date = datetime.utcnow().isoformat()

            # Determine category from URL
            category = "general"
            if "/colombia/" in url:
                category = "colombia"
            elif "/bogota/" in url:
                category = "bogota"
            elif "/politica/" in url:
                category = "politics"
            elif "/economia/" in url:
                category = "economy"
            elif "/internacional/" in url:
                category = "international"
            elif "/deportes/" in url:
                category = "sports"

            # Extract tags
            tags = self.extract_tags(soup)

            # Get metadata
            metadata = self.extract_metadata(soup)

            return {
                "title": title,
                "content": content,
                "author": author,
                "published_date": published_date,
                "category": category,
                "url": url,
                "source": self.name,
                "tags": tags,
                "metadata": metadata,
                "content_hash": self.generate_content_hash(content),
                "scraped_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error parsing article {url}: {str(e)}")
            return None

    def scrape(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Main scraping method

        Args:
            limit: Maximum number of articles to scrape

        Returns:
            List of scraped article dictionaries
        """
        logger.info(f"Starting scrape for {self.name}")
        scraped_items = []

        try:
            # Get article URLs
            article_urls = self.get_article_urls(limit=limit)
            logger.info(f"Found {len(article_urls)} articles to scrape")

            # Scrape each article
            for i, url in enumerate(article_urls, 1):
                logger.info(f"Scraping article {i}/{len(article_urls)}: {url}")

                html = self.fetch_page(url)
                if not html:
                    continue

                soup = self.parse_html(html)
                article_data = self.parse_article(soup, url)

                if article_data:
                    scraped_items.append(article_data)
                    logger.info(f"Successfully scraped: {article_data['title'][:60]}...")

                # Rate limiting
                time.sleep(self.rate_limit_delay)

        except Exception as e:
            logger.error(f"Error during scraping {self.name}: {str(e)}")

        logger.info(f"Completed scraping {self.name}: {len(scraped_items)} articles")
        return scraped_items


# Example usage
if __name__ == "__main__":
    scraper = RCNRadioScraper()
    articles = scraper.scrape(limit=10)

    print(f"\nScraped {len(articles)} articles from RCN Radio")
    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"Author: {article['author']}")
        print(f"Category: {article['category']}")
        print(f"Published: {article['published_date']}")
        print(f"URL: {article['url']}")
        print(f"Content length: {len(article['content'])} chars")
        print(f"Tags: {', '.join(article['tags'][:5])}")
