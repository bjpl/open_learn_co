"""
El Universal newspaper scraper implementation
Cartagena's leading newspaper and Caribbean coast regional news source
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class ElUniversalScraper(SmartScraper):
    """Scraper for El Universal (eluniversal.com.co)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'El Universal',
            'url': 'https://www.eluniversal.com.co',
            'rate_limit': '10/minute'
        }
        super().__init__(config)

        self.sections = [
            'cartagena',
            'bolivar',
            'caribe',
            'colombia',
            'politica',
            'economia',
            'deportes',
            'cultura',
            'turismo'
        ]

        # CSS selectors for El Universal structure
        self.selectors = {
            'article_links': '.article-link, .story-link, .card-link, .news-link, h2 a, h3 a',
            'title': 'h1.article-title, h1.story-title, h1.news-title, h1',
            'subtitle': '.article-subtitle, .story-subtitle, '.bajada', .entradilla',
            'content': '.article-content, .story-content, .content-body, .news-content',
            'author': '.article-author, .story-author, .byline, .autor',
            'date': '.article-date, .story-date, time, .fecha',
            'category': '.article-category, .story-category, .seccion',
            'tags': '.article-tags a, .story-tags a, .etiquetas a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from El Universal homepage"""
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

        # Get articles from Cartagena and Caribbean sections
        for section in self.sections[:6]:  # Focus on regional sections
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
        """Check if URL is a valid El Universal article"""
        # Article indicators
        article_indicators = [
            '/cartagena/',
            '/bolivar/',
            '/caribe/',
            '/colombia/',
            '/politica/',
            '/economia/',
            '/deportes/',
            '/cultura/',
            '/turismo/',
            '/articulo/',
            '/noticia/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/autor/',
            '/tag/',
            '/tema/',
            '/seccion/',
            '/multimedia/',
            '/video/',
            '/galeria/',
            '/opinion/',
            '/columnista/',
            '/especiales/',
            '/directorio/',
            '#',
            'mailto:',
            'javascript:',
            '.pdf',
            '.jpg',
            '.png',
            'twitter.com',
            'facebook.com',
            'instagram.com'
        ]

        # Check indicators
        has_indicator = any(indicator in url.lower() for indicator in article_indicators)

        # Check exclusions
        should_exclude = any(pattern in url.lower() for pattern in exclude_patterns)

        # Check for article ID pattern
        has_id = bool(re.search(r'/\d{5,}', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from El Universal article"""
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
                    # Skip promotional content
                    if not self._is_promotional_content(text):
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

            # Cartagena and Bolívar specific analysis
            entities = self._extract_bolivar_entities(content)
            tourism_focus = self._analyze_tourism_focus(content, url)
            difficulty = self._calculate_coastal_difficulty(content)

            # Create document
            doc = ScrapedDocument(
                source=self.source_name,
                source_type='regional_newspaper',
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                metadata={
                    'category': category,
                    'bolivar_entities': entities,
                    'tourism_focus': tourism_focus,
                    'word_count': len(content.split()),
                    'region': 'Bolívar',
                    'city_focus': 'Cartagena',
                    'caribbean_coast': True,
                    'heritage_city': True
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Bolívar',
                categories=[category] if category else ['regional']
            )

            return doc

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    def _is_promotional_content(self, text: str) -> bool:
        """Check if text is promotional content"""
        promo_indicators = [
            'suscríbete',
            'premium',
            'descarga la app',
            'síguenos',
            'boletín',
            'newsletter',
            'contenido patrocinado',
            'publicidad',
            'el universal digital'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in promo_indicators)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        author_selectors = [
            '.article-author',
            '.story-author',
            '.byline',
            '.autor',
            '.redaccion'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                # Clean prefixes
                author_text = re.sub(r'^(Por:?\s*|Redacción\s*|@)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return author_text

        return "El Universal"

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
        date_selectors = ['.article-date', '.story-date', '.fecha']
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
                if category and category.lower() not in ['inicio', 'home', 'el universal']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                section_map = {
                    'cartagena': 'Cartagena',
                    'bolivar': 'Bolívar',
                    'caribe': 'Caribe',
                    'colombia': 'Nacional',
                    'politica': 'Política',
                    'economia': 'Economía',
                    'deportes': 'Deportes',
                    'cultura': 'Cultura',
                    'turismo': 'Turismo'
                }
                return section_map.get(section, section.title())

        return 'Regional'

    def _extract_bolivar_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Bolívar and Cartagena specific entities"""
        entities = {}

        patterns = {
            'local_politicians': [
                r'\b(William Dau|Dumek Turbay|Vicente Blel)\b',
                r'\b(Pedrito Pereira|Manolo Duque|Ana Bolívar)\b'
            ],
            'local_institutions': [
                r'\b(Alcaldía de Cartagena|Gobernación de Bolívar)\b',
                r'\b(Concejo de Cartagena|Asamblea de Bolívar)\b',
                r'\b(Universidad de Cartagena|Universidad Tecnológica)\b',
                r'\b(Aguas de Cartagena|Electricaribe|Gases del Caribe)\b'
            ],
            'municipalities': [
                r'\b(Cartagena|Magangué|Turbaco|Arjona)\b',
                r'\b(El Carmen de Bolívar|San Pablo|Simití)\b',
                r'\b(Santa Rosa|Clemencia|Villanueva|Mahates)\b'
            ],
            'neighborhoods_zones': [
                r'\b(Bocagrande|Castillogrande|Manga|Getsemaní)\b',
                r'\b(Centro Histórico|Ciudad Amurallada|San Diego)\b',
                r'\b(Pie de la Popa|El Pozón|Nelson Mandela)\b'
            ],
            'tourism_heritage': [
                r'\b(Ciudad Amurallada|Patrimonio de la Humanidad)\b',
                r'\b(Castillo San Felipe|Palacio de la Inquisición)\b',
                r'\b(Torre del Reloj|Plaza Santo Domingo)\b',
                r'\b(Islas del Rosario|Isla Barú|Playa Blanca)\b'
            ],
            'companies_organizations': [
                r'\b(Reficar|Zona Franca|Terminal de Contenedores)\b',
                r'\b(Comfenalco|Mamonal|Corpoturismo)\b',
                r'\b(Festival de Música|Hay Festival)\b'
            ],
            'cultural_events': [
                r'\b(Festival de Música|Miss Colombia|Hay Festival)\b',
                r'\b(Independencia de Cartagena|Fiestas Novembrinas)\b',
                r'\b(Festival de Cine|Teatro Heredia)\b'
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

    def _analyze_tourism_focus(self, content: str, url: str) -> Dict[str, Any]:
        """Analyze tourism and heritage focus"""
        focus_analysis = {}

        content_lower = content.lower()

        # Tourism indicators
        tourism_indicators = [
            'turismo', 'turista', 'hotel', 'crucero', 'patrimonio',
            'unesco', 'amurallada', 'colonial', 'visitante'
        ]

        # Heritage indicators
        heritage_indicators = [
            'patrimonio', 'unesco', 'histórico', 'colonial', 'monumento',
            'muralla', 'castillo', 'convento', 'iglesia', 'restauración'
        ]

        # Port and commerce indicators
        port_indicators = ['puerto', 'contenedor', 'exportación', 'zona franca', 'reficar']

        tourism_count = sum(1 for indicator in tourism_indicators if indicator in content_lower)
        heritage_count = sum(1 for indicator in heritage_indicators if indicator in content_lower)
        port_count = sum(1 for indicator in port_indicators if indicator in content_lower)

        total_indicators = max(1, tourism_count + heritage_count + port_count)

        focus_analysis['tourism_ratio'] = tourism_count / total_indicators
        focus_analysis['heritage_ratio'] = heritage_count / total_indicators
        focus_analysis['port_ratio'] = port_count / total_indicators

        # Determine primary focus
        if focus_analysis['tourism_ratio'] > 0.4:
            focus_analysis['primary_focus'] = 'tourism'
        elif focus_analysis['heritage_ratio'] > 0.3:
            focus_analysis['primary_focus'] = 'heritage'
        elif focus_analysis['port_ratio'] > 0.3:
            focus_analysis['primary_focus'] = 'commerce'
        else:
            focus_analysis['primary_focus'] = 'general'

        # UNESCO and heritage content detection
        unesco_terms = ['unesco', 'patrimonio mundial', 'patrimonio de la humanidad', 'histórico']
        unesco_count = sum(1 for term in unesco_terms if term in content_lower)
        focus_analysis['unesco_content'] = unesco_count > 0
        focus_analysis['heritage_relevance'] = min(1.0, unesco_count / 4)

        return focus_analysis

    def _calculate_coastal_difficulty(self, text: str) -> float:
        """Calculate difficulty for Cartagena coastal content"""
        if not text:
            return 2.3

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Cartagena-specific factors
        local_names = len(re.findall(r'\b[A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)*\b', text))
        heritage_terms = len(re.findall(r'\b(patrimonio|unesco|colonial|histórico|restauración)\b', text, re.IGNORECASE))
        tourism_terms = len(re.findall(r'\b(turismo|hotel|crucero|visitante|atracción)\b', text, re.IGNORECASE))
        costeño_expressions = len(re.findall(r'\b(chevere|bacano|que tal|pues|mijo|papá)\b', text, re.IGNORECASE))

        # Start with base for coastal heritage city
        difficulty = 2.2

        # Sentence complexity
        if avg_sentence_length > 17:
            difficulty += 0.3
        if avg_sentence_length > 25:
            difficulty += 0.3

        # Word complexity
        if avg_word_length > 6.2:
            difficulty += 0.2

        # Regional factors
        difficulty += min(0.4, local_names / 60)  # Historical names can be complex
        difficulty += min(0.4, heritage_terms / 15)  # Heritage terminology
        difficulty -= min(0.2, tourism_terms / 20)  # Tourism content is often accessible
        difficulty -= min(0.2, costeño_expressions / 15)  # Coastal expressions

        return min(5.0, max(1.0, difficulty))

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for Cartagena news"""
        if score < 2.1:
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
        """Parse Spanish date formats"""
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
            r'(\d{4})-(\d{2})-(\d{2})'                 # "2024-01-15"
        ]

        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if '/' in pattern:
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