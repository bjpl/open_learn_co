"""
El Espectador newspaper scraper implementation
Colombia's second-largest national newspaper - left-leaning perspective
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class ElEspectadorScraper(SmartScraper):
    """Scraper for El Espectador (elespectador.com)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'El Espectador',
            'url': 'https://www.elespectador.com',
            'rate_limit': '10/minute'
        }
        super().__init__(config)

        self.sections = [
            'politica',
            'economia',
            'justicia',
            'bogota',
            'nacional',
            'mundo',
            'deportes',
            'cultura',
            'ambiente',
            'salud'
        ]

        # CSS selectors for El Espectador's structure
        # Note: El Espectador uses JSON-LD structured data as primary source
        self.selectors = {
            'article_links': 'a[href*="/politica/"], a[href*="/economia/"], a[href*="/justicia/"], h2 a, h3 a',
            'title': 'h1',
            'content': 'article p',
            'author': 'a[href*="/autores/"]',
            'date': 'time',
            'category': 'a[href*="/politica/"], a[href*="/economia/"]',
            'json_ld': 'script[type="application/ld+json"]'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from El Espectador homepage"""
        soup = self.parse_html(homepage_html)
        urls = set()

        # Get main articles
        article_links = soup.select(self.selectors['article_links'])

        for link in article_links:
            href = link.get('href', '')
            if href:
                if href.startswith('/'):
                    href = self.base_url + href
                if self._is_article_url(href):
                    urls.add(href)

        # Also scrape section pages for more articles
        for section in self.sections[:3]:  # Limit to avoid too many requests
            section_url = f"{self.base_url}/{section}"
            section_html = self.fetch_page(section_url)
            if section_html:
                section_soup = self.parse_html(section_html)
                section_links = section_soup.select(self.selectors['article_links'])

                for link in section_links:
                    href = link.get('href', '')
                    if href:
                        if href.startswith('/'):
                            href = self.base_url + href
                        if self._is_article_url(href):
                            urls.add(href)

        return list(urls)

    def _is_article_url(self, url: str) -> bool:
        """Check if URL is a valid article"""
        # El Espectador article patterns
        article_indicators = [
            '/noticias/',
            '/politica/',
            '/economia/',
            '/justicia/',
            '/nacional/',
            '/mundo/',
            '/deportes/',
            '/cultura/',
            '/ambiente/',
            '/salud/',
            '/bogota/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/tag/',
            '/autor/',
            '/seccion/',
            '/multimedia/',
            '/podcast/',
            '/live/',
            '/video/',
            '#',
            'mailto:',
            'javascript:',
            '.pdf',
            '.jpg',
            '.png'
        ]

        # Check article indicators
        has_article_indicator = any(indicator in url for indicator in article_indicators)

        # Check exclusions
        should_exclude = any(pattern in url for pattern in exclude_patterns)

        # Check for article ID pattern (numbers in URL)
        has_id_pattern = bool(re.search(r'/\d{4,}', url))

        return (has_article_indicator or has_id_pattern) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from El Espectador article"""
        soup = self.parse_html(article_html)

        try:
            # Try JSON-LD extraction first (most reliable for El Espectador)
            json_ld_doc = self._extract_from_json_ld(soup, url)
            if json_ld_doc:
                return json_ld_doc

            # Fallback to HTML extraction
            logger.info(f"JSON-LD extraction failed, trying HTML for {url}")

            # Extract title
            title_elem = soup.select_one(self.selectors['title'])
            if not title_elem:
                logger.warning(f"No title found for {url}")
                return None
            title = self._clean_text(title_elem.get_text())

            # Extract content from article paragraphs
            article_elem = soup.find('article')
            if not article_elem:
                logger.warning(f"No article element found for {url}")
                return None

            # Get paragraphs and filter content
            paragraphs = article_elem.find_all('p')
            content_parts = []

            for p in paragraphs:
                text = self._clean_text(p.get_text())
                # Filter out noise: short paragraphs, audio notices, "Lea también" links
                if (text and len(text) > 50 and
                    'Audio generado' not in text and
                    'Lea también' not in text and
                    'Sugerimos' not in text[:20]):
                    content_parts.append(text)

            content = ' '.join(content_parts)

            # Check for minimal content
            if len(content) < 200:
                logger.warning(f"Content too short for {url}: {len(content)} chars")
                return None

            # Extract metadata
            author = self._extract_author(soup)
            published_date = self._extract_date(soup, url)
            category = self._extract_category(soup, url)

            # Extract Colombian entities and analysis
            entities = self._extract_colombian_entities(content)
            difficulty = self._calculate_difficulty(content)

            # Create document
            doc = ScrapedDocument(
                source=self.source_name,
                source_type='newspaper',
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                metadata={
                    'category': category,
                    'entities': entities,
                    'word_count': len(content.split()),
                    'source_bias': 'center-left'
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Colombia',
                categories=[category] if category else ['general']
            )

            return doc

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    def _extract_from_json_ld(self, soup: BeautifulSoup, url: str) -> Optional[ScrapedDocument]:
        """Extract article data from JSON-LD structured data"""
        try:
            import json

            # Find all JSON-LD scripts
            scripts = soup.find_all('script', type='application/ld+json')

            for script in scripts:
                if not script.string:
                    continue

                try:
                    data = json.loads(script.string)

                    # Look for NewsArticle schema
                    if data.get('@type') != 'NewsArticle':
                        continue

                    # Extract required fields
                    title = data.get('headline', '').strip()
                    content = data.get('articleBody', '').strip()

                    if not title or not content or len(content) < 200:
                        continue

                    # Extract author
                    author_data = data.get('author', {})
                    if isinstance(author_data, list):
                        author = author_data[0].get('name', 'El Espectador') if author_data else 'El Espectador'
                    else:
                        author = author_data.get('name', 'El Espectador')

                    # Extract published date - return as DateTime object, not string
                    published_date = data.get('datePublished')
                    if published_date:
                        # Parse and convert to naive datetime for database
                        try:
                            dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                            published_date = dt.replace(tzinfo=None) if dt.tzinfo else dt
                        except Exception as e:
                            logger.warning(f"Error parsing date {published_date}: {e}")
                            published_date = None
                    else:
                        published_date = None

                    # Extract category from URL
                    category = self._extract_category(soup, url)

                    # Extract Colombian entities and calculate difficulty
                    entities = self._extract_colombian_entities(content)
                    difficulty = self._calculate_difficulty(content)

                    # Create document
                    doc = ScrapedDocument(
                        source=self.source_name,
                        source_type='newspaper',
                        url=url,
                        title=title,
                        content=content,
                        author=author,
                        published_date=published_date,
                        metadata={
                            'category': category,
                            'entities': entities,
                            'word_count': len(content.split()),
                            'source_bias': 'center-left',
                            'extraction_method': 'json-ld'
                        },
                        language='es',
                        difficulty_level=self._get_difficulty_level(difficulty),
                        region='Colombia',
                        categories=[category] if category else ['general']
                    )

                    logger.info(f"Successfully extracted article via JSON-LD: {title[:50]}...")
                    return doc

                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error extracting from JSON-LD for {url}: {e}")
            return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author from HTML"""
        author_elem = soup.select_one(self.selectors['author'])
        if author_elem:
            author_text = self._clean_text(author_elem.get_text())
            # Clean up common prefixes
            author_text = re.sub(r'^(Por:?\s*|Redacción\s*)', '', author_text, flags=re.IGNORECASE)
            return author_text if author_text else None
        return "El Espectador"

    def _extract_date(self, soup: BeautifulSoup, url: str) -> Optional[datetime]:
        """Extract publication date from HTML"""
        date_elem = soup.select_one(self.selectors['date'])

        if date_elem:
            # Try datetime attribute first
            datetime_attr = date_elem.get('datetime', '')
            if datetime_attr:
                try:
                    # Handle both Z and timezone offset formats
                    return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                except Exception as e:
                    logger.debug(f"Error parsing datetime attribute {datetime_attr}: {e}")

            # Try to parse text
            date_text = self._clean_text(date_elem.get_text())
            if date_text:
                parsed_date = self._parse_spanish_date(date_text)
                if parsed_date:
                    return parsed_date

        # Try to extract from URL
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if date_match:
            year, month, day = date_match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except Exception as e:
                logger.debug(f"Error parsing date from URL: {e}")

        logger.warning(f"Could not extract date for {url}, using current time")
        return datetime.utcnow()

    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        # Try breadcrumbs or category elements
        category_elem = soup.select_one(self.selectors['category'])
        if category_elem:
            category = self._clean_text(category_elem.get_text())
            if category and category.lower() not in ['inicio', 'home', 'el espectador']:
                return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                return section.replace('-', ' ').title()

        return 'General'

    def _extract_colombian_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Colombian-specific entities"""
        entities = {}

        patterns = {
            'politicians': [
                r'\b(Gustavo Petro|Francia Márquez|Iván Duque|Álvaro Uribe|Juan Manuel Santos)\b',
                r'\b(César Gaviria|Andrés Pastrana|Ernesto Samper)\b'
            ],
            'institutions': [
                r'\b(Presidencia|Casa de Nariño|Congreso|Senado|Cámara)\b',
                r'\b(Fiscalía|Procuraduría|Contraloría|CNE|Registraduría)\b',
                r'\b(Corte Suprema|Corte Constitucional|Consejo de Estado)\b',
                r'\b(FARC|ELN|Clan del Golfo|AGC)\b'
            ],
            'locations': [
                r'\b(Bogotá|Medellín|Cali|Barranquilla|Cartagena|Cúcuta|Bucaramanga)\b',
                r'\b(Antioquia|Valle|Cundinamarca|Atlántico|Santander|Chocó|Nariño)\b',
                r'\b(Arauca|Casanare|Meta|Putumayo|Amazonas|Guainía|Vichada)\b'
            ],
            'organizations': [
                r'\b(Ecopetrol|Avianca|Bancolombia|EPM|ETB)\b',
                r'\b(DANE|Banco de la República|Mindefensa|Minsalud)\b'
            ]
        }

        for entity_type, pattern_list in patterns.items():
            found = set()
            for pattern in pattern_list:
                matches = re.findall(pattern, text, re.IGNORECASE)
                found.update(matches)
            if found:
                entities[entity_type] = list(found)

        return entities

    def _calculate_difficulty(self, text: str) -> float:
        """Calculate text difficulty for language learners"""
        if not text:
            return 1.0

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Complex patterns
        complex_words = len(re.findall(r'\b\w{10,}\b', text))
        technical_terms = len(re.findall(r'\b[A-Z]{2,}\b', text))

        # Calculate score
        difficulty = 1.0

        if avg_sentence_length > 15:
            difficulty += 0.5
        if avg_sentence_length > 25:
            difficulty += 0.5

        if avg_word_length > 6:
            difficulty += 0.5
        if avg_word_length > 8:
            difficulty += 0.5

        difficulty += min(1.0, complex_words / 100)
        difficulty += min(0.5, technical_terms / 50)

        return min(5.0, difficulty)

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level"""
        if score < 2.0:
            return 'Principiante'
        elif score < 3.0:
            return 'Intermedio'
        elif score < 4.0:
            return 'Avanzado'
        else:
            return 'Experto'

    def _parse_spanish_date(self, date_text: str) -> Optional[datetime]:
        """Parse Spanish date formats"""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        # Pattern: "15 de enero de 2024"
        match = re.search(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', date_text)
        if match:
            day, month_name, year = match.groups()
            month = months.get(month_name.lower())
            if month:
                try:
                    return datetime(int(year), month, int(day))
                except:
                    pass

        return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove unwanted characters
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()