"""
Base scraper class with common functionality for all Colombian content sources
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import hashlib
import json

from app.config import settings
from scrapers.base.rate_limiter import RateLimiter
from app.database.models import ScrapedContent


logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for content scrapers"""

    def __init__(self, source_config: Dict[str, Any]):
        self.name = source_config["name"]
        self.base_url = source_config["url"]
        self.category = source_config["category"]
        self.scrape_interval = source_config.get("scrape_interval", 60)
        self.rate_limiter = RateLimiter(max_requests=10, time_window=60)
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "User-Agent": settings.USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page with rate limiting and error handling"""
        await self.rate_limiter.acquire()

        try:
            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup"""
        return BeautifulSoup(html, 'lxml')

    def generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()

    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract common metadata from HTML"""
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

        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords:
            metadata["keywords"] = keywords.get("content", "").split(",")

        # Publication date
        pub_date = soup.find("meta", attrs={"property": "article:published_time"})
        if pub_date:
            metadata["published_time"] = pub_date.get("content", "")

        return metadata

    @abstractmethod
    async def get_article_urls(self) -> List[str]:
        """Get list of article URLs to scrape - must be implemented by subclasses"""
        pass

    @abstractmethod
    def parse_article(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse article content - must be implemented by subclasses"""
        pass

    async def scrape(self) -> List[ScrapedContent]:
        """Main scraping method"""
        logger.info(f"Starting scrape for {self.name}")
        scraped_items = []

        try:
            # Get article URLs
            article_urls = await self.get_article_urls()
            logger.info(f"Found {len(article_urls)} articles to scrape from {self.name}")

            # Scrape each article
            for url in article_urls[:50]:  # Increased limit for content ingestion
                html = await self.fetch_page(url)
                if html:
                    soup = self.parse_html(html)
                    article_data = self.parse_article(soup, url)

                    if article_data:
                        # Add metadata
                        article_data["source"] = self.name
                        article_data["source_url"] = url
                        article_data["category"] = self.category
                        # Make scraped_at timezone-naive to match database expectations
                        article_data["scraped_at"] = datetime.utcnow().replace(tzinfo=None)
                        article_data["content_hash"] = self.generate_content_hash(
                            article_data.get("content", "")
                        )

                        # Extract additional metadata and merge with existing extra_metadata
                        metadata = self.extract_metadata(soup)
                        if "extra_metadata" not in article_data:
                            article_data["extra_metadata"] = {}
                        article_data["extra_metadata"].update(metadata)

                        # Ensure published_date is DateTime and timezone-naive
                        if "published_date" in article_data:
                            if isinstance(article_data["published_date"], str):
                                from dateutil import parser as date_parser
                                try:
                                    parsed_date = date_parser.isoparse(article_data["published_date"])
                                    # Remove timezone to make it naive (database uses naive datetimes)
                                    article_data["published_date"] = parsed_date.replace(tzinfo=None)
                                except:
                                    article_data["published_date"] = None
                            elif hasattr(article_data["published_date"], 'tzinfo') and article_data["published_date"].tzinfo:
                                # If it's already a datetime with timezone, strip the timezone
                                article_data["published_date"] = article_data["published_date"].replace(tzinfo=None)

                        scraped_items.append(ScrapedContent(**article_data))

                # Small delay between requests
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error during scraping {self.name}: {str(e)}")

        logger.info(f"Completed scraping {self.name}: {len(scraped_items)} articles")
        return scraped_items

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""

        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove common noise
        text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")

        return text.strip()