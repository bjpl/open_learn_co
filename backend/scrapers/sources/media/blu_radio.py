"""
Blu Radio news scraper implementation
Colombia's leading radio news network
"""

import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class BluRadioScraper(SmartScraper):
    """Scraper for Blu Radio (bluradio.com)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'Blu Radio',
            'url': 'https://www.bluradio.com',
            'rate_limit': '12/minute'
        }
        super().__init__(config)

        self.sections = [
            'nacion',
            'politica',
            'judicial',
            'economia',
            'internacional',
            'deportes',
            'bogota',
            'antioquia',
            'valle',
            'santander'
        ]

        # CSS selectors for Blu Radio's structure
        self.selectors = {
            'article_links': '.article-link, .story-link, '.card-link', .noticia-link, h2 a, h3 a',
            'title': 'h1.article-title, h1.story-title, h1.title, h1',
            'subtitle': '.article-subtitle, .story-subtitle, .bajada, .entradilla',
            'content': '.article-content, .story-content, .content-body, .noticia-texto',
            'author': '.article-author, .story-author, .author, .redactor',
            'date': '.article-date, '.story-date', time, .fecha-publicacion',
            'category': '.article-category, .story-category, .seccion',
            'tags': '.article-tags a, .story-tags a, .etiquetas a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from Blu Radio homepage"""
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

        # Get articles from regional and news sections
        for section in self.sections[:6]:  # Limit requests
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
        """Check if URL is a valid Blu Radio article"""
        # News article indicators
        article_indicators = [
            '/nacion/',
            '/politica/',
            '/judicial/',
            '/economia/',
            '/internacional/',
            '/deportes/',
            '/bogota/',
            '/antioquia/',
            '/valle/',
            '/santander/',
            '/noticia/',
            '/articulo/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/programas/',
            '/emisoras/',
            '/audio/',
            '/podcast/',
            '/video/',
            '/multimedia/',
            '/opinion/',
            '/columnistas/',
            '/tag/',
            '/autor/',
            '/programa/',
            '#',
            'mailto:',
            'javascript:',
            '.mp3',
            '.mp4',
            '.pdf',
            '.jpg',
            '.png',
            'twitter.com',
            'facebook.com',
            'instagram.com',
            'youtube.com'
        ]

        # Check indicators
        has_indicator = any(indicator in url.lower() for indicator in article_indicators)

        # Check exclusions
        should_exclude = any(pattern in url.lower() for pattern in exclude_patterns)

        # Check for article ID pattern
        has_id = bool(re.search(r'/\d{5,}', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from Blu Radio article"""
        soup = self.parse_html(article_html)

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

            # Process content
            content_parts = []
            if subtitle:
                content_parts.append(subtitle)

            paragraphs = content_elem.find_all(['p', 'div'])
            for p in paragraphs:
                text = self._clean_text(p.get_text())
                if text and len(text) > 25:
                    # Skip radio promotional content
                    if not self._is_radio_promotional_content(text):
                        content_parts.append(text)

            content = ' '.join(content_parts)

            # Validate content
            if len(content) < 200:
                logger.warning(f"Content too short for {url}")
                return None

            # Extract metadata
            author = self._extract_author(soup)
            published_date = self._extract_date(soup, url)
            category = self._extract_category(soup, url)

            # Radio news specific analysis
            entities = self._extract_regional_entities(content)
            news_type = self._classify_news_type(content, url)
            difficulty = self._calculate_radio_difficulty(content)

            # Create document
            doc = ScrapedDocument(
                source=self.source_name,
                source_type='radio_news',
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                metadata={
                    'category': category,
                    'regional_entities': entities,
                    'news_type': news_type,
                    'word_count': len(content.split()),
                    'source_type': 'radio',
                    'regional_focus': True,
                    'content_style': 'journalistic'
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Colombia',
                categories=[category] if category else ['noticias']
            )

            return doc

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    def _is_radio_promotional_content(self, text: str) -> bool:
        """Check if text is radio promotional content"""
        radio_promo_indicators = [
            'escucha en vivo',
            'sintoniza',
            'frecuencia',
            'descarga la app',
            'suscríbete',
            'escucha el programa',
            'en el aire',
            'transmisión en vivo',
            'podcast completo',
            'audio disponible',
            'síguenos en redes',
            'blu radio',
            'mañanas blu'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in radio_promo_indicators)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        author_selectors = [
            '.article-author',
            '.story-author',
            '.author',
            '.redactor',
            '.byline',
            '.firma'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                # Clean prefixes
                author_text = re.sub(r'^(Por:?\s*|Redacción\s*|@|De:\s*)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return author_text

        return "Blu Radio"

    def _extract_date(self, soup: BeautifulSoup, url: str) -> Optional[datetime]:
        """Extract publication date"""
        # Try time element
        time_elem = soup.select_one('time')
        if time_elem and time_elem.get('datetime'):
            try:
                return datetime.fromisoformat(time_elem.get('datetime').replace('Z', '+00:00'))
            except:
                pass

        # Try date selectors
        date_selectors = ['.article-date', '.story-date', '.fecha-publicacion', '.fecha']
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
        category_selectors = ['.article-category', '.story-category', '.seccion']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category and category.lower() not in ['inicio', 'home', 'blu radio']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                section_map = {
                    'nacion': 'Nacional',
                    'politica': 'Política',
                    'judicial': 'Judicial',
                    'economia': 'Economía',
                    'internacional': 'Internacional',
                    'deportes': 'Deportes',
                    'bogota': 'Bogotá',
                    'antioquia': 'Antioquia',
                    'valle': 'Valle del Cauca',
                    'santander': 'Santander'
                }
                return section_map.get(section, section.title())

        return 'Noticias'

    def _extract_regional_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract regional and local entities"""
        entities = {}

        patterns = {
            'national_figures': [
                r'\b(Gustavo Petro|Francia Márquez|Iván Duque|Álvaro Uribe)\b',
                r'\b(Juan Manuel Santos|César Gaviria|Andrés Pastrana)\b'
            ],
            'regional_politicians': [
                r'\b(Daniel Quintero|Federico Gutiérrez|Jorge Iván Ospina)\b',
                r'\b(Claudia López|Enrique Peñalosa|Samuel Moreno)\b',
                r'\b(Luis Pérez|Sergio Fajardo|Aníbal Gaviria)\b'
            ],
            'cities_municipalities': [
                r'\b(Bogotá|Medellín|Cali|Barranquilla|Cartagena)\b',
                r'\b(Bucaramanga|Cúcuta|Pereira|Manizales|Armenia)\b',
                r'\b(Ibagué|Neiva|Pasto|Popayán|Montería)\b',
                r'\b(Villavicencio|Tunja|Valledupar|Sincelejo)\b'
            ],
            'departments': [
                r'\b(Antioquia|Valle del Cauca|Cundinamarca|Atlántico)\b',
                r'\b(Santander|Norte de Santander|Bolívar|Córdoba)\b',
                r'\b(Chocó|Nariño|Cauca|Huila|Tolima|Meta)\b',
                r'\b(Caldas|Risaralda|Quindío|Boyacá|Casanare)\b'
            ],
            'institutions': [
                r'\b(Alcaldía|Gobernación|Concejo|Asamblea)\b',
                r'\b(Policía Metropolitana|CTI|SIJIN|GAULA)\b',
                r'\b(Personería|Defensoría|Contraloría Regional)\b'
            ],
            'transport_infrastructure': [
                r'\b(Metro|Metrocable|MIO|Transmilenio|SITP)\b',
                r'\b(aeropuerto|terminal|puerto|vía|autopista)\b',
                r'\b(El Dorado|José María Córdova|Alfonso Bonilla)\b'
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

    def _classify_news_type(self, content: str, url: str) -> str:
        """Classify the type of news based on content and URL"""
        content_lower = content.lower()

        # Breaking news indicators
        breaking_indicators = ['última hora', 'urgente', 'en desarrollo', 'confirma', 'anuncia']
        if any(indicator in content_lower for indicator in breaking_indicators):
            return 'breaking_news'

        # Political news
        political_indicators = ['congreso', 'senado', 'presidente', 'ministro', 'elecciones', 'votación']
        if any(indicator in content_lower for indicator in political_indicators) or '/politica/' in url:
            return 'political'

        # Judicial news
        judicial_indicators = ['fiscalía', 'juez', 'condena', 'investigación', 'captura', 'proceso judicial']
        if any(indicator in content_lower for indicator in judicial_indicators) or '/judicial/' in url:
            return 'judicial'

        # Economic news
        economic_indicators = ['economía', 'empresa', 'mercado', 'inversión', 'empleo', 'inflación']
        if any(indicator in content_lower for indicator in economic_indicators) or '/economia/' in url:
            return 'economic'

        # Sports news
        if '/deportes/' in url or any(word in content_lower for word in ['fútbol', 'ciclismo', 'atlético', 'selección']):
            return 'sports'

        # Regional news
        regional_indicators = ['alcalde', 'gobernador', 'concejo', 'región', 'departamento']
        if any(indicator in content_lower for indicator in regional_indicators):
            return 'regional'

        return 'general'

    def _calculate_radio_difficulty(self, text: str) -> float:
        """Calculate difficulty for radio news content"""
        if not text:
            return 2.3  # Radio news tends to be accessible

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Radio-specific factors
        quoted_speech = len(re.findall(r'"[^"]*"', text))  # Direct quotes
        conversational_words = len(re.findall(r'\b(dijo|explicó|comentó|manifestó|señaló|indicó)\b', text, re.IGNORECASE))
        technical_terms = len(re.findall(r'\b\w{11,}\b', text))
        regional_terms = len(re.findall(r'\b(alcaldía|gobernación|concejo|personería)\b', text, re.IGNORECASE))

        # Start with base for radio content
        difficulty = 2.2

        # Sentence complexity
        if avg_sentence_length > 18:
            difficulty += 0.3
        if avg_sentence_length > 28:
            difficulty += 0.4

        # Word complexity
        if avg_word_length > 6.5:
            difficulty += 0.3

        # Content factors
        difficulty -= min(0.4, quoted_speech / 20)  # Quotes make it easier
        difficulty -= min(0.3, conversational_words / 30)  # Conversational style is easier
        difficulty += min(0.5, technical_terms / 60)  # Technical terms harder
        difficulty += min(0.2, regional_terms / 20)  # Regional terms add slight complexity

        return min(5.0, max(1.0, difficulty))

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for radio news"""
        if score < 2.0:
            return 'Principiante'
        elif score < 2.7:
            return 'Intermedio'
        elif score < 3.4:
            return 'Intermedio-Avanzado'
        elif score < 4.0:
            return 'Avanzado'
        else:
            return 'Experto'

    def _parse_spanish_date(self, date_text: str) -> Optional[datetime]:
        """Parse Spanish date formats including relative times"""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        # Date patterns
        patterns = [
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',  # "15 de enero de 2024"
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',          # "enero 15, 2024"
            r'(\d{1,2})/(\d{1,2})/(\d{4})',            # "15/01/2024"
            r'(\d{4})-(\d{2})-(\d{2})',                # "2024-01-15"
            r'Hace\s+(\d+)\s+(hora|día|minuto)s?',     # "Hace 2 horas"
            r'(\d+)\s+(hora|día|minuto)s?\s+atrás',    # "2 horas atrás"
            r'Hoy\s+(\d{1,2}):(\d{2})',                # "Hoy 14:30"
            r'Ayer\s+(\d{1,2}):(\d{2})'                # "Ayer 14:30"
        ]

        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if 'Hace' in pattern or 'atrás' in pattern:
                        # Handle relative time
                        amount, unit = match.groups()
                        amount = int(amount)
                        now = datetime.utcnow()
                        if 'hora' in unit:
                            return now - timedelta(hours=amount)
                        elif 'día' in unit:
                            return now - timedelta(days=amount)
                        elif 'minuto' in unit:
                            return now - timedelta(minutes=amount)
                    elif 'Hoy' in pattern:
                        hour, minute = match.groups()
                        today = datetime.utcnow().date()
                        return datetime.combine(today, datetime.min.time().replace(hour=int(hour), minute=int(minute)))
                    elif 'Ayer' in pattern:
                        hour, minute = match.groups()
                        yesterday = datetime.utcnow().date() - timedelta(days=1)
                        return datetime.combine(yesterday, datetime.min.time().replace(hour=int(hour), minute=int(minute)))
                    elif '/' in pattern:
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    elif '-' in pattern:
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                    else:
                        if 'de' in pattern:
                            day, month_name, year = match.groups()
                            month = months.get(month_name.lower())
                        else:
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

        # Remove extra whitespace
        text = ' '.join(text.split())
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()