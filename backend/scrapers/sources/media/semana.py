"""
Semana magazine scraper implementation
Colombia's leading political and current affairs magazine
"""

import re
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class SemanaScraper(SmartScraper):
    """Scraper for Semana magazine (semana.com)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'Semana',
            'url': 'https://www.semana.com',
            'rate_limit': '8/minute'
        }
        super().__init__(config)

        self.sections = [
            'nacion',
            'politica',
            'economia',
            'mundo',
            'cultura',
            'deportes',
            'tecnologia',
            'opinion',
            'investigacion'
        ]

        # CSS selectors for Semana's structure
        self.selectors = {
            'article_links': '.card-link, .article-link, .story-link, h2 a, h3 a',
            'title': 'h1.article-title, h1.story-title, h1.title, h1',
            'subtitle': '.article-subtitle, .story-subtitle, .bajada, .lead',
            'content': '.article-body, .story-content, .content-body, .article-text',
            'author': '.article-author, .story-author, .author-name, .byline',
            'date': '.article-date, .story-date, time, .publish-date',
            'category': '.article-category, .story-category, .section-name',
            'tags': '.article-tags a, .story-tags a, .tags a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from Semana homepage"""
        soup = self.parse_html(homepage_html)
        urls = set()

        # Extract from homepage
        article_links = soup.select(self.selectors['article_links'])

        for link in article_links:
            href = link.get('href', '')
            if href:
                if href.startswith('/'):
                    href = self.base_url + href
                if self._is_article_url(href):
                    urls.add(href)

        # Get articles from main sections
        for section in self.sections[:4]:  # Limit requests
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
        """Check if URL is a valid Semana article"""
        # Article indicators
        article_indicators = [
            '/articulo/',
            '/nacion/',
            '/politica/',
            '/economia/',
            '/mundo/',
            '/cultura/',
            '/deportes/',
            '/investigacion/',
            '/opinion/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/autor/',
            '/tag/',
            '/seccion/',
            '/especial/',
            '/podcast/',
            '/multimedia/',
            '/video/',
            '/galeria/',
            '#',
            'mailto:',
            'javascript:',
            '.pdf',
            '.jpg',
            '.png',
            'twitter.com',
            'facebook.com'
        ]

        # Check indicators
        has_indicator = any(indicator in url.lower() for indicator in article_indicators)

        # Check exclusions
        should_exclude = any(pattern in url.lower() for pattern in exclude_patterns)

        # Check for article ID pattern
        has_id = bool(re.search(r'/\d{6,}/', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from Semana article using JSON-LD first, then HTML fallback"""
        soup = self.parse_html(article_html)

        try:
            # Try JSON-LD first (most reliable)
            json_ld_data = self._extract_json_ld(soup)
            if json_ld_data:
                return self._create_document_from_json_ld(json_ld_data, url, soup)

            # Fallback to HTML parsing
            return self._extract_from_html(soup, url)

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract JSON-LD NewsArticle data"""
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if data.get('@type') in ['NewsArticle', 'Article']:
                    return data
            except Exception as e:
                logger.debug(f"Failed to parse JSON-LD: {e}")
                continue
        return None

    def _create_document_from_json_ld(self, data: Dict, url: str, soup: BeautifulSoup) -> Optional[ScrapedDocument]:
        """Create document from JSON-LD data"""
        # Extract basic fields
        title = data.get('headline', '')
        if not title:
            logger.warning(f"No title in JSON-LD for {url}")
            return None

        # Get article body
        content = data.get('articleBody', '')
        description = data.get('description', '')

        if not content:
            logger.warning(f"No articleBody in JSON-LD for {url}")
            return None

        # Combine description and content
        if description and description not in content:
            content = f"{description} {content}"

        # Extract author
        author_data = data.get('author', {})
        if isinstance(author_data, dict):
            author = author_data.get('name', 'Semana')
        elif isinstance(author_data, list) and author_data:
            author = author_data[0].get('name', 'Semana') if isinstance(author_data[0], dict) else str(author_data[0])
        else:
            author = str(author_data) if author_data else 'Semana'

        # Extract published date - return as DateTime object, not string
        published_date = data.get('datePublished')
        if published_date:
            # Parse and convert to naive datetime for database
            try:
                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                published_date = dt.replace(tzinfo=None) if dt.tzinfo else dt
            except:
                published_date = None

        if not published_date:
            published_date = self._extract_date(soup, url)

        # Extract category
        category = self._extract_category(soup, url)

        # Extract entities and analysis
        entities = self._extract_colombian_entities(content)
        difficulty = self._calculate_difficulty(content)
        political_bias = self._detect_political_bias(content)

        # Create document
        doc = ScrapedDocument(
            source=self.source_name,
            source_type='magazine',
            url=url,
            title=title,
            content=content,
            author=author,
            published_date=published_date,
            metadata={
                'category': category,
                'entities': entities,
                'word_count': len(content.split()),
                'source_bias': 'center-right',
                'political_content': political_bias,
                'content_type': 'analysis' if 'opinion' in url else 'news',
                'extraction_method': 'json-ld'
            },
            language='es',
            difficulty_level=self._get_difficulty_level(difficulty),
            region='Colombia',
            categories=[category] if category else ['política']
        )

        return doc

    def _extract_from_html(self, soup: BeautifulSoup, url: str) -> Optional[ScrapedDocument]:
        """Extract content from HTML (fallback method)"""
        # Updated selectors for current Semana structure
        title_elem = soup.find('h1')
        if not title_elem:
            logger.warning(f"No title found for {url}")
            return None
        title = self._clean_text(title_elem.get_text())

        # Find article element
        article_elem = soup.find('article')
        if not article_elem:
            logger.warning(f"No article element found for {url}")
            return None

        # Extract all paragraphs from article
        content_parts = []
        paragraphs = article_elem.find_all('p')
        for p in paragraphs:
            text = self._clean_text(p.get_text())
            if text and len(text) > 30:  # Filter short paragraphs
                # Skip ads and promotional content
                if not self._is_promotional_content(text):
                    content_parts.append(text)

        content = ' '.join(content_parts)

        # Check content quality
        if len(content) < 300:
            logger.warning(f"Content too short for {url}")
            return None

        # Check for paywall
        if self._is_paywall_content(content):
            logger.info(f"Paywall detected for {url}")

        # Extract metadata
        author = self._extract_author(soup)
        published_date = self._extract_date(soup, url)
        category = self._extract_category(soup, url)

        # Extract entities and analysis
        entities = self._extract_colombian_entities(content)
        difficulty = self._calculate_difficulty(content)
        political_bias = self._detect_political_bias(content)

        # Create document
        doc = ScrapedDocument(
            source=self.source_name,
            source_type='magazine',
            url=url,
            title=title,
            content=content,
            author=author,
            published_date=published_date,
            metadata={
                'category': category,
                'entities': entities,
                'word_count': len(content.split()),
                'source_bias': 'center-right',
                'political_content': political_bias,
                'content_type': 'analysis' if 'opinion' in url else 'news',
                'extraction_method': 'html'
            },
            language='es',
            difficulty_level=self._get_difficulty_level(difficulty),
            region='Colombia',
            categories=[category] if category else ['política']
        )

        return doc

    def _is_promotional_content(self, text: str) -> bool:
        """Check if text is promotional/advertising content"""
        promo_indicators = [
            'suscríbete',
            'premium',
            'descarga la app',
            'síguenos en',
            'nuestras redes',
            'lee también',
            'contenido relacionado',
            'publicidad'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in promo_indicators)

    def _is_paywall_content(self, content: str) -> bool:
        """Check if content is behind paywall"""
        paywall_indicators = [
            'contenido exclusivo',
            'suscríbete para',
            'acceso ilimitado',
            'hazte suscriptor',
            'contenido premium'
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in paywall_indicators)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        # Try multiple author selectors
        author_selectors = [
            '.article-author',
            '.story-author',
            '.author-name',
            '.byline',
            '.autor'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                # Clean up common prefixes
                author_text = re.sub(r'^(Por:?\s*|Redacción\s*|@)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return author_text

        return "Semana"

    def _extract_date(self, soup: BeautifulSoup, url: str) -> Optional[datetime]:
        """Extract publication date"""
        # Try time element first
        time_elem = soup.select_one('time')
        if time_elem and time_elem.get('datetime'):
            try:
                return datetime.fromisoformat(time_elem.get('datetime').replace('Z', '+00:00'))
            except:
                pass

        # Try other date selectors
        date_selectors = ['.article-date', '.story-date', '.publish-date', '.fecha']
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = self._clean_text(date_elem.get_text())
                parsed_date = self._parse_spanish_date(date_text)
                if parsed_date:
                    return parsed_date

        # Extract from URL
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if date_match:
            year, month, day = date_match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except:
                pass

        return datetime.utcnow()

    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        # Try category elements
        category_selectors = ['.article-category', '.story-category', '.section-name']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category and category.lower() not in ['inicio', 'home', 'semana']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                return section.replace('-', ' ').title()

        return 'Política'

    def _extract_colombian_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Colombian political and social entities"""
        entities = {}

        patterns = {
            'political_figures': [
                r'\b(Gustavo Petro|Francia Márquez|Iván Duque|Álvaro Uribe)\b',
                r'\b(Juan Manuel Santos|César Gaviria|Andrés Pastrana)\b',
                r'\b(Sergio Fajardo|Rodolfo Hernández|Fico Gutiérrez)\b'
            ],
            'political_parties': [
                r'\b(Pacto Histórico|Centro Democrático|Partido Liberal|Partido Conservador)\b',
                r'\b(Cambio Radical|Polo Democrático|Verde|Colombia Humana)\b'
            ],
            'institutions': [
                r'\b(Presidencia|Casa de Nariño|Congreso|Senado)\b',
                r'\b(Fiscalía|Procuraduría|Contraloría|CNE)\b',
                r'\b(Corte Suprema|Corte Constitucional)\b',
                r'\b(FARC|ELN|Clan del Golfo)\b'
            ],
            'regions': [
                r'\b(Bogotá|Medellín|Cali|Barranquilla|Cartagena)\b',
                r'\b(Antioquia|Valle|Cundinamarca|Atlántico|Santander)\b',
                r'\b(Chocó|Nariño|Cauca|Norte de Santander)\b'
            ],
            'economic_entities': [
                r'\b(Ecopetrol|Banco de la República|DANE|DNP)\b',
                r'\b(Avianca|Bancolombia|Grupo Éxito|EPM)\b'
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

    def _detect_political_bias(self, text: str) -> Dict[str, float]:
        """Detect political bias indicators in content"""
        # Keywords for different political orientations
        left_keywords = [
            'derechos humanos', 'justicia social', 'igualdad', 'progresista',
            'cambio social', 'izquierda', 'popular'
        ]

        right_keywords = [
            'libre mercado', 'empresa privada', 'inversión', 'crecimiento económico',
            'tradicional', 'orden', 'seguridad'
        ]

        center_keywords = [
            'consenso', 'diálogo', 'moderado', 'equilibrio', 'centro'
        ]

        text_lower = text.lower()

        left_score = sum(1 for keyword in left_keywords if keyword in text_lower)
        right_score = sum(1 for keyword in right_keywords if keyword in text_lower)
        center_score = sum(1 for keyword in center_keywords if keyword in text_lower)

        total = max(1, left_score + right_score + center_score)

        return {
            'left': left_score / total,
            'right': right_score / total,
            'center': center_score / total
        }

    def _calculate_difficulty(self, text: str) -> float:
        """Calculate text difficulty for language learners"""
        if not text:
            return 3.0  # Default to intermediate

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Complex patterns
        complex_words = len(re.findall(r'\b\w{12,}\b', text))
        political_terms = len(re.findall(r'\b(constitucional|democracia|institucional|legislativo|ejecutivo|judicial)\b', text, re.IGNORECASE))

        # Calculate score (Semana tends to be more complex)
        difficulty = 2.5  # Start higher for magazine content

        if avg_sentence_length > 20:
            difficulty += 0.5
        if avg_sentence_length > 30:
            difficulty += 0.5

        if avg_word_length > 7:
            difficulty += 0.3

        difficulty += min(0.7, complex_words / 100)
        difficulty += min(0.5, political_terms / 50)

        return min(5.0, difficulty)

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level"""
        if score < 2.5:
            return 'Intermedio'
        elif score < 3.5:
            return 'Intermedio-Avanzado'
        elif score < 4.5:
            return 'Avanzado'
        else:
            return 'Experto'

    def _parse_spanish_date(self, date_text: str) -> Optional[datetime]:
        """Parse Spanish date formats"""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        # Various date patterns
        patterns = [
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',  # "15 de enero de 2024"
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',          # "enero 15, 2024"
            r'(\d{1,2})/(\d{1,2})/(\d{4})'             # "15/01/2024"
        ]

        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if '/' in pattern:  # Numeric format
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    else:  # Text format
                        if 'de' in pattern:  # Spanish format
                            day, month_name, year = match.groups()
                            month = months.get(month_name.lower())
                        else:  # English format
                            month_name, day, year = match.groups()
                            month = months.get(month_name.lower())

                        if month:
                            return datetime(int(year), month, int(day))
                except:
                    continue

        return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()