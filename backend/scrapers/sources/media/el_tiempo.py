"""
El Tiempo newspaper scraper implementation
Colombia's largest national newspaper
"""

import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ElTiempoScraper(BaseScraper):
    """Scraper for El Tiempo (eltiempo.com)"""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.sections = [
            'politica',
            'economia',
            'justicia',
            'bogota',
            'colombia',
            'internacional',
            'deportes',
            'cultura'
        ]

        # CSS selectors specific to El Tiempo's structure
        self.selectors = {
            'article_links': 'article a, h2 a, h3 a',
            'title': 'h1.titulo, h1[class*="title"], h1',
            'subtitle': 'h2.sumario, .lead, .article-lead',
            'content': '.articulo-contenido, .article-body, .content-body',
            'author': '.autor-nombre, .author-name, .by-author',
            'date': '.fecha, time, .published-date',
            'category': '.categoria, .section-name',
            'tags': '.tags a, .article-tags a'
        }

        # Colombian entities patterns
        self.colombian_patterns = {
            'institutions': [
                r'\b(MinDefensa|Mindefensa|Ministerio de Defensa)\b',
                r'\b(Fiscalía|Fiscalia)\b',
                r'\b(Procuraduría|Procuraduria)\b',
                r'\b(Contraloría|Contraloria)\b',
                r'\b(Congreso|Senado|Cámara de Representantes)\b',
                r'\b(Corte Suprema|Corte Constitucional)\b',
                r'\b(Presidencia|Casa de Nariño)\b',
                r'\b(DANE|Banco de la República)\b',
                r'\b(FARC|ELN|EPL)\b',
                r'\b(Policía Nacional|Ejército Nacional|Armada Nacional|Fuerza Aérea)\b'
            ],
            'locations': [
                r'\b(Bogotá|Medellín|Cali|Barranquilla|Cartagena|Cúcuta|Bucaramanga)\b',
                r'\b(Antioquia|Valle del Cauca|Cundinamarca|Atlántico|Santander)\b',
                r'\b(Amazonas|Chocó|Nariño|Cauca|Meta|Arauca|Putumayo)\b'
            ],
            'political_figures': [
                r'\b(Petro|Gustavo Petro)\b',
                r'\b(Francia Márquez|Francia Marquez)\b',
                r'\b(Iván Duque|Ivan Duque)\b',
                r'\b(Álvaro Uribe|Alvaro Uribe)\b',
                r'\b(Juan Manuel Santos)\b'
            ],
            'economic_terms': [
                r'\b(peso colombiano|COP|pesos)\b',
                r'\b(UVR|UVT|salario mínimo)\b',
                r'\b(Ecopetrol|Avianca|Grupo Éxito)\b',
                r'\b(café|petróleo|carbón|oro|esmeraldas)\b'
            ]
        }

    async def get_article_urls(self) -> List[str]:
        """Get list of article URLs from El Tiempo sections"""
        all_urls = set()

        for section in self.sections:
            section_url = f"{self.base_url}/{section}"
            logger.info(f"Fetching section: {section_url}")

            html = await self.fetch_page(section_url)
            if html:
                soup = self.parse_html(html)
                links = soup.select(self.selectors['article_links'])

                for link in links:
                    href = link.get('href', '')
                    if href:
                        # Handle relative URLs
                        if href.startswith('/'):
                            href = self.base_url + href
                        # Filter for article URLs
                        if self._is_article_url(href):
                            all_urls.add(href)

        return list(all_urls)

    def _is_article_url(self, url: str) -> bool:
        """Check if URL is likely an article"""
        # El Tiempo article patterns
        article_patterns = [
            r'/\d{4}/\d{2}/\d{2}/',  # Date pattern
            r'/article/',
            r'/noticia/',
            r'-\d{6,}',  # Article ID pattern
        ]

        # Exclude patterns
        exclude_patterns = [
            r'/tema/',
            r'/seccion/',
            r'/autor/',
            r'/multimedia/',
            r'/podcast/',
            r'/opinion/',
            r'#',
            r'mailto:',
        ]

        # Check if URL matches article pattern
        has_article_pattern = any(re.search(pattern, url) for pattern in article_patterns)

        # Check if URL should be excluded
        should_exclude = any(re.search(pattern, url) for pattern in exclude_patterns)

        return has_article_pattern and not should_exclude

    def parse_article(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse El Tiempo article content using JSON-LD structured data with HTML fallback"""
        try:
            # Try JSON-LD extraction first (preferred method)
            article = self._extract_from_json_ld(soup, url)

            if article:
                logger.info(f"Successfully extracted article from JSON-LD: {url}")
            else:
                # Fallback to HTML parsing
                logger.info(f"JSON-LD extraction failed, falling back to HTML parsing: {url}")
                article = self._extract_from_html(soup, url)

            if not article:
                logger.warning(f"Failed to extract article content: {url}")
                return None

            # Enrich article with Colombian entities and learning metrics
            content_text = article.get('content', '')

            # Check for paywall
            if self._is_paywall_content(content_text):
                article['is_paywall'] = True
                logger.info(f"Paywall detected for {url}")

            # Extract Colombian entities
            article['colombian_entities'] = self._extract_colombian_entities(content_text)

            # Calculate difficulty score for language learning
            article['difficulty_score'] = self._calculate_difficulty(content_text)

            # Word count for language learning
            article['word_count'] = len(content_text.split())

            # Extract category
            if 'category' not in article:
                article['category'] = self._extract_category(url, soup)

            return article

        except Exception as e:
            logger.error(f"Error parsing article {url}: {str(e)}")
            return None

    def _extract_from_json_ld(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Extract article data from JSON-LD structured data"""
        try:
            # Find all JSON-LD script tags
            json_ld_scripts = soup.find_all('script', type='application/ld+json')

            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)

                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        data = data[0] if data else {}

                    # Check if this is a NewsArticle or ReportageNewsArticle
                    article_type = data.get('@type', '')
                    if article_type not in ['NewsArticle', 'ReportageNewsArticle', 'Article']:
                        continue

                    article = {
                        'extra_metadata': {}  # Initialize for storing non-standard fields
                    }

                    # Extract headline (required)
                    headline = data.get('headline') or data.get('name')
                    if not headline:
                        continue
                    article['title'] = self.clean_text(headline)

                    # Extract article body (required)
                    article_body = data.get('articleBody')
                    if not article_body:
                        continue
                    article['content'] = self.clean_text(article_body)

                    # Extract description/subtitle
                    description = data.get('description')
                    article['subtitle'] = self.clean_text(description) if description else ""

                    # Extract published date
                    published_date = data.get('datePublished')
                    if published_date:
                        article['published_date'] = self._normalize_iso_date(published_date)
                    else:
                        article['published_date'] = None
                        logger.warning(f"No datePublished in JSON-LD for {url}")

                    # Extract author
                    author_data = data.get('author')
                    if author_data:
                        if isinstance(author_data, dict):
                            article['author'] = self.clean_text(author_data.get('name', 'El Tiempo'))
                        elif isinstance(author_data, list) and author_data:
                            # Get first author if multiple
                            first_author = author_data[0]
                            if isinstance(first_author, dict):
                                article['author'] = self.clean_text(first_author.get('name', 'El Tiempo'))
                            else:
                                article['author'] = self.clean_text(str(first_author))
                        else:
                            article['author'] = "El Tiempo"
                    else:
                        article['author'] = "El Tiempo"

                    # Extract image (store in metadata for database compatibility)
                    image_data = data.get('image')
                    image_url = None
                    if image_data:
                        if isinstance(image_data, dict):
                            image_url = image_data.get('url')
                        elif isinstance(image_data, list) and image_data:
                            first_image = image_data[0]
                            if isinstance(first_image, dict):
                                image_url = first_image.get('url')
                            else:
                                image_url = str(first_image)
                        elif isinstance(image_data, str):
                            image_url = image_data

                    if image_url:
                        article['extra_metadata']['image_url'] = image_url

                    # Extract keywords as tags
                    keywords = data.get('keywords')
                    if keywords:
                        if isinstance(keywords, str):
                            article['tags'] = [k.strip() for k in keywords.split(',')]
                        elif isinstance(keywords, list):
                            article['tags'] = [self.clean_text(str(k)) for k in keywords]
                    else:
                        article['tags'] = []

                    # Extract section/category
                    section = data.get('articleSection')
                    if section:
                        article['category'] = self.clean_text(section)

                    logger.info(f"Successfully extracted article from JSON-LD: {article['title']}")
                    return article

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON-LD: {str(e)}")
                    continue
                except Exception as e:
                    logger.warning(f"Error extracting from JSON-LD: {str(e)}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Error in JSON-LD extraction: {str(e)}")
            return None

    def _extract_from_html(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Fallback HTML extraction method"""
        try:
            article = {
                'extra_metadata': {}  # Initialize for storing non-standard fields
            }

            # Extract title
            title_elem = soup.select_one(self.selectors['title'])
            if not title_elem:
                logger.warning(f"No title found for {url}")
                return None
            article['title'] = self.clean_text(title_elem.get_text())

            # Extract subtitle
            subtitle_elem = soup.select_one(self.selectors['subtitle'])
            article['subtitle'] = self.clean_text(subtitle_elem.get_text()) if subtitle_elem else ""

            # Extract content
            content_elem = soup.select_one(self.selectors['content'])
            if not content_elem:
                logger.warning(f"No content found for {url}")
                return None

            # Get all paragraphs from content
            paragraphs = content_elem.find_all('p')
            content_text = ' '.join([self.clean_text(p.get_text()) for p in paragraphs])
            article['content'] = content_text

            # Extract author
            author_elem = soup.select_one(self.selectors['author'])
            article['author'] = self.clean_text(author_elem.get_text()) if author_elem else "El Tiempo"

            # Extract date
            date_elem = soup.select_one(self.selectors['date'])
            if date_elem:
                article['published_date'] = self._parse_date(date_elem)
            else:
                article['published_date'] = None
                logger.warning(f"No date found for {url}")

            # Extract tags
            tags = soup.select(self.selectors['tags'])
            article['tags'] = [self.clean_text(tag.get_text()) for tag in tags]

            return article

        except Exception as e:
            logger.error(f"Error in HTML extraction: {str(e)}")
            return None

    def _is_paywall_content(self, content: str) -> bool:
        """Check if content is behind paywall"""
        paywall_indicators = [
            'suscríbete',
            'contenido exclusivo',
            'acceso ilimitado',
            'hazte suscriptor',
            'lee esta historia'
        ]

        content_lower = content.lower()
        # Short content might indicate paywall
        if len(content) < 200:
            return True

        # Check for paywall keywords
        return any(indicator in content_lower for indicator in paywall_indicators)

    def _normalize_iso_date(self, date_str: str) -> str:
        """Normalize ISO date string to consistent format"""
        try:
            # Parse various ISO formats
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.isoformat()
        except Exception as e:
            logger.warning(f"Failed to normalize date '{date_str}': {str(e)}")
            return date_str

    def _parse_date(self, date_elem) -> Optional[str]:
        """Parse date from various formats - returns None if parsing fails"""
        try:
            date_text = self.clean_text(date_elem.get_text())

            # Try to parse ISO format from datetime attribute
            if date_elem.get('datetime'):
                return self._normalize_iso_date(date_elem.get('datetime'))

            # Spanish month names to numbers
            spanish_months = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }

            # Colombian date format: "15 de enero de 2024"
            match = re.search(r'(\d{1,2}) de (\w+) de (\d{4})', date_text)
            if match:
                day = int(match.group(1))
                month_name = match.group(2).lower()
                year = int(match.group(3))

                month = spanish_months.get(month_name)
                if month:
                    date_obj = datetime(year, month, day)
                    return date_obj.isoformat()

            # Numeric date format: "15/01/2024"
            match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_text)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                date_obj = datetime(year, month, day)
                return date_obj.isoformat()

            # If no pattern matched, return None instead of current time
            logger.warning(f"Could not parse date from text: {date_text}")
            return None

        except Exception as e:
            logger.error(f"Error parsing date: {str(e)}")
            return None

    def _extract_category(self, url: str, soup: BeautifulSoup) -> str:
        """Extract article category"""
        # Try to get from page
        category_elem = soup.select_one(self.selectors['category'])
        if category_elem:
            return self.clean_text(category_elem.get_text())

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url:
                return section

        return 'general'

    def _extract_colombian_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Colombian-specific entities from text"""
        entities = {}

        for entity_type, patterns in self.colombian_patterns.items():
            found_entities = set()
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                found_entities.update(matches)

            if found_entities:
                entities[entity_type] = list(found_entities)

        return entities

    def _calculate_difficulty(self, text: str) -> float:
        """
        Calculate text difficulty for language learners
        Based on sentence length, word frequency, and complexity
        """
        if not text:
            return 0.0

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Basic metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Difficulty factors
        difficulty = 0.0

        # Sentence length factor (longer = harder)
        if avg_sentence_length < 10:
            difficulty += 1.0  # Simple
        elif avg_sentence_length < 20:
            difficulty += 2.0  # Intermediate
        elif avg_sentence_length < 30:
            difficulty += 3.0  # Advanced
        else:
            difficulty += 4.0  # Expert

        # Word length factor
        if avg_word_length < 5:
            difficulty += 0.5
        elif avg_word_length < 7:
            difficulty += 1.0
        else:
            difficulty += 1.5

        # Complex vocabulary indicators
        complex_indicators = [
            r'\b\w{12,}\b',  # Very long words
            r'\b[A-Z]{3,}\b',  # Acronyms
            r'\d+[,.]?\d*%?',  # Numbers and percentages
        ]

        for indicator in complex_indicators:
            matches = re.findall(indicator, text)
            difficulty += len(matches) * 0.1

        # Normalize to 1-5 scale
        difficulty = min(5.0, max(1.0, difficulty))

        return round(difficulty, 1)