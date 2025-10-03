"""
El Espectador news scraper for Colombian Intelligence Platform
Scrapes articles from https://www.elespectador.com
"""

import time
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElEspectadorScraper:
    """Scraper for El Espectador news website"""

    def __init__(self):
        self.base_url = "https://www.elespectador.com"
        self.name = "El Espectador"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Colombian entities for extraction
        self.colombian_cities = [
            'Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena',
            'Cúcuta', 'Bucaramanga', 'Pereira', 'Manizales', 'Ibagué',
            'Santa Marta', 'Villavicencio', 'Pasto', 'Neiva', 'Armenia'
        ]

        self.colombian_departments = [
            'Antioquia', 'Valle del Cauca', 'Cundinamarca', 'Atlántico',
            'Bolívar', 'Santander', 'Norte de Santander', 'Tolima',
            'Risaralda', 'Caldas', 'Magdalena', 'Meta', 'Nariño', 'Huila'
        ]

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page with error handling"""
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup"""
        return BeautifulSoup(html, 'html.parser')

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove common noise
        text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        return text.strip()

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Colombian entities from text"""
        entities = {
            "cities": [],
            "departments": []
        }

        # Extract cities
        for city in self.colombian_cities:
            if city in text:
                entities["cities"].append(city)

        # Extract departments
        for dept in self.colombian_departments:
            if dept in text:
                entities["departments"].append(dept)

        return entities

    def extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/keywords from article"""
        tags = []

        # Try meta keywords
        keywords_meta = soup.find("meta", attrs={"name": "keywords"})
        if keywords_meta and keywords_meta.get("content"):
            tags.extend([k.strip() for k in keywords_meta["content"].split(",")])

        # Try article tags
        tag_elements = soup.find_all("a", class_=re.compile(r"tag|etiqueta", re.I))
        for tag_el in tag_elements:
            tag_text = self.clean_text(tag_el.get_text())
            if tag_text and tag_text not in tags:
                tags.append(tag_text)

        return tags[:10]  # Limit to 10 tags

    def generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()

    def get_article_urls(self, limit: int = 20) -> List[str]:
        """Get list of article URLs from homepage and section pages"""
        article_urls = []

        # Main sections to scrape
        sections = [
            "",  # Homepage
            "/noticias",
            "/politica",
            "/economia",
            "/judicial",
            "/colombia",
        ]

        for section in sections:
            if len(article_urls) >= limit:
                break

            url = f"{self.base_url}{section}"
            logger.info(f"Fetching articles from: {url}")

            html = self.fetch_page(url)
            if not html:
                continue

            soup = self.parse_html(html)

            # Find article links
            # El Espectador uses various patterns for article links
            article_links = soup.find_all("a", href=re.compile(r"/(noticias|politica|economia|judicial|colombia|deportes|entretenimiento)/"))

            for link in article_links:
                href = link.get("href", "")

                # Ensure full URL
                if href.startswith("/"):
                    href = self.base_url + href
                elif not href.startswith("http"):
                    continue

                # Filter out non-article URLs
                if any(skip in href for skip in ["/galeria/", "/video/", "/autor/", "/tag/"]):
                    continue

                if href not in article_urls:
                    article_urls.append(href)

                    if len(article_urls) >= limit:
                        break

            # Rate limiting between sections
            time.sleep(1)

        logger.info(f"Found {len(article_urls)} article URLs")
        return article_urls[:limit]

    def parse_article(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse individual article content"""
        try:
            # Extract title
            title = None
            title_selectors = [
                ("h1", {"class": re.compile(r"title|titulo|headline", re.I)}),
                ("h1", {}),
                ("meta", {"property": "og:title"}),
            ]

            for selector, attrs in title_selectors:
                if selector == "meta":
                    elem = soup.find(selector, attrs)
                    if elem:
                        title = elem.get("content", "")
                        break
                else:
                    elem = soup.find(selector, attrs)
                    if elem:
                        title = self.clean_text(elem.get_text())
                        break

            if not title:
                logger.warning(f"No title found for {url}")
                return None

            # Extract subtitle/summary
            subtitle = ""
            subtitle_selectors = [
                ("h2", {"class": re.compile(r"subtitle|bajada|sumario", re.I)}),
                ("p", {"class": re.compile(r"lead|summary|bajada", re.I)}),
                ("meta", {"property": "og:description"}),
            ]

            for selector, attrs in subtitle_selectors:
                if selector == "meta":
                    elem = soup.find(selector, attrs)
                    if elem:
                        subtitle = elem.get("content", "")
                        break
                else:
                    elem = soup.find(selector, attrs)
                    if elem:
                        subtitle = self.clean_text(elem.get_text())
                        break

            # Extract content
            content_parts = []
            content_selectors = [
                ("div", {"class": re.compile(r"article-body|content|texto|cuerpo", re.I)}),
                ("div", {"itemprop": "articleBody"}),
            ]

            content_container = None
            for selector, attrs in content_selectors:
                content_container = soup.find(selector, attrs)
                if content_container:
                    break

            if content_container:
                # Extract all paragraphs
                paragraphs = content_container.find_all("p")
                for p in paragraphs:
                    text = self.clean_text(p.get_text())
                    if text and len(text) > 20:  # Filter short fragments
                        content_parts.append(text)

            content = " ".join(content_parts)

            if not content:
                logger.warning(f"No content found for {url}")
                return None

            # Extract author
            author = "El Espectador"
            author_selectors = [
                ("span", {"class": re.compile(r"author|autor|firma", re.I)}),
                ("a", {"rel": "author"}),
                ("meta", {"name": "author"}),
            ]

            for selector, attrs in author_selectors:
                if selector == "meta":
                    elem = soup.find(selector, attrs)
                    if elem:
                        author = elem.get("content", "El Espectador")
                        break
                else:
                    elem = soup.find(selector, attrs)
                    if elem:
                        author = self.clean_text(elem.get_text())
                        break

            # Extract published date
            published_date = datetime.now().isoformat()
            date_selectors = [
                ("time", {"datetime": True}),
                ("meta", {"property": "article:published_time"}),
                ("span", {"class": re.compile(r"date|fecha|time", re.I)}),
            ]

            for selector, attrs in date_selectors:
                elem = soup.find(selector, attrs)
                if elem:
                    if selector == "time":
                        published_date = elem.get("datetime", "")
                    elif selector == "meta":
                        published_date = elem.get("content", "")
                    else:
                        date_text = self.clean_text(elem.get_text())
                        if date_text:
                            published_date = date_text

                    if published_date:
                        break

            # Extract category
            category = "General"
            # Try to extract from URL
            url_parts = url.split("/")
            if len(url_parts) > 3:
                potential_category = url_parts[3]
                if potential_category in ["politica", "economia", "judicial", "colombia", "noticias"]:
                    category = potential_category.capitalize()

            # Try from breadcrumb or meta
            breadcrumb = soup.find("nav", {"class": re.compile(r"breadcrumb", re.I)})
            if breadcrumb:
                links = breadcrumb.find_all("a")
                if len(links) > 1:
                    category = self.clean_text(links[1].get_text())

            # Calculate word count
            word_count = len(content.split())

            # Extract entities and tags
            entities = self.extract_entities(content)
            tags = self.extract_tags(soup)

            # Build article data
            article_data = {
                "title": title,
                "subtitle": subtitle,
                "content": content,
                "author": author,
                "published_date": published_date,
                "category": category,
                "url": url,
                "source": self.name,
                "word_count": word_count,
                "content_hash": self.generate_content_hash(content),
                "scraped_at": datetime.now().isoformat(),
                "entities": entities,
                "tags": tags,
            }

            logger.info(f"Successfully parsed: {title[:50]}...")
            return article_data

        except Exception as e:
            logger.error(f"Error parsing article {url}: {str(e)}")
            return None

    def scrape(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Main scraping method

        Args:
            limit: Maximum number of articles to scrape

        Returns:
            List of scraped article data
        """
        logger.info(f"Starting scrape for {self.name}")
        scraped_articles = []

        try:
            # Get article URLs
            article_urls = self.get_article_urls(limit=limit)

            # Scrape each article
            for idx, url in enumerate(article_urls, 1):
                logger.info(f"Scraping article {idx}/{len(article_urls)}: {url}")

                html = self.fetch_page(url)
                if not html:
                    continue

                soup = self.parse_html(html)
                article_data = self.parse_article(soup, url)

                if article_data:
                    scraped_articles.append(article_data)

                # Rate limiting: 1 second between requests
                time.sleep(1)

        except Exception as e:
            logger.error(f"Error during scraping {self.name}: {str(e)}")

        logger.info(f"Completed scraping {self.name}: {len(scraped_articles)} articles")
        return scraped_articles


if __name__ == "__main__":
    # Test the scraper
    scraper = ElEspectadorScraper()
    articles = scraper.scrape(limit=5)

    print(f"\nScraped {len(articles)} articles from El Espectador")
    for article in articles:
        print(f"\n---")
        print(f"Title: {article['title']}")
        print(f"Author: {article['author']}")
        print(f"Category: {article['category']}")
        print(f"Word Count: {article['word_count']}")
        print(f"Tags: {', '.join(article['tags'][:3])}")
        print(f"URL: {article['url']}")
