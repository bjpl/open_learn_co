"""
El Heraldo newspaper scraper implementation
Barranquilla's leading newspaper and Caribbean coast regional news source
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class ElHeraldoScraper(SmartScraper):
    """Scraper for El Heraldo (elheraldo.co)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'El Heraldo',
            'url': 'https://www.elheraldo.co',
            'rate_limit': '10/minute'
        }
        super().__init__(config)

        self.sections = [
            'barranquilla',
            'atlantico',
            'caribe',
            'colombia',
            'politica',
            'economia',
            'deportes',
            'cultura',
            'local'
        ]

        # CSS selectors for El Heraldo structure
        self.selectors = {
            'article_links': '.article-link, .story-link, .card-link, .nota-link, h2 a, h3 a',
            'title': 'h1.article-title, h1.story-title, h1.titulo-nota, h1',
            'subtitle': '.article-subtitle, .story-subtitle, .bajada, .entradilla',
            'content': '.article-content, .story-content, .content-body, .contenido-nota',
            'author': '.article-author, .story-author, .byline, .autor',
            'date': '.article-date, .story-date, time, .fecha',
            'category': '.article-category, .story-category, .seccion',
            'tags': '.article-tags a, .story-tags a, .etiquetas a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from El Heraldo homepage"""
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

        # Get articles from Caribbean and regional sections
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
        """Check if URL is a valid El Heraldo article"""
        # Article indicators
        article_indicators = [
            '/barranquilla/',
            '/atlantico/',
            '/caribe/',
            '/colombia/',
            '/politica/',
            '/economia/',
            '/deportes/',
            '/cultura/',
            '/local/',
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
            '/transmision/',
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
        """Extract content from El Heraldo article"""
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

            # Caribbean coast specific analysis
            entities = self._extract_caribbean_entities(content)
            regional_focus = self._analyze_caribbean_focus(content, url)
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
                    'caribbean_entities': entities,
                    'coastal_focus': regional_focus,
                    'word_count': len(content.split()),
                    'region': 'Atlántico',
                    'city_focus': 'Barranquilla',
                    'caribbean_coast': True
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Atlántico',
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
            'el heraldo premium'
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

        return "El Heraldo"

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
                if category and category.lower() not in ['inicio', 'home', 'el heraldo']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                section_map = {
                    'barranquilla': 'Barranquilla',
                    'atlantico': 'Atlántico',
                    'caribe': 'Caribe',
                    'colombia': 'Nacional',
                    'politica': 'Política',
                    'economia': 'Economía',
                    'deportes': 'Deportes',
                    'cultura': 'Cultura',
                    'local': 'Local'
                }
                return section_map.get(section, section.title())

        return 'Regional'

    def _extract_caribbean_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Caribbean coast and Atlántico specific entities"""
        entities = {}

        patterns = {
            'local_politicians': [
                r'\b(Jaime Pumarejo|Alejandro Char|Eduardo Verano)\b',
                r'\b(Elsa Noguera|Alex Char|Arturo Char)\b',
                r'\b(Shakira Navarro|Pumarejo|José Dumek)\b'
            ],
            'local_institutions': [
                r'\b(Alcaldía de Barranquilla|Gobernación del Atlántico)\b',
                r'\b(Concejo de Barranquilla|Asamblea del Atlántico)\b',
                r'\b(Universidad del Norte|Uninorte|Universidad Libre)\b',
                r'\b(CRA|Triple A|Electricaribe|Air-e)\b'
            ],
            'municipalities': [
                r'\b(Barranquilla|Soledad|Malambo|Puerto Colombia)\b',
                r'\b(Galapa|Tubará|Usiacurí|Polonuevo)\b',
                r'\b(Sabanagrande|Sabanalarga|Juan de Acosta)\b'
            ],
            'neighborhoods_zones': [
                r'\b(El Prado|Riomar|Villa Country|Alto Prado)\b',
                r'\b(La Cumbre|Villa Santos|Boston|Rebolo)\b',
                r'\b(Sur Occidente|Metropolitano|Centro Histórico)\b'
            ],
            'companies_organizations': [
                r'\b(Organización Soledad|Tecnoglass|Cementos Argos)\b',
                r'\b(Comfamiliar|Combarranquilla|Cámara de Comercio)\b',
                r'\b(Terminal Marítimo|Puerto de Barranquilla)\b'
            ],
            'caribbean_entities': [
                r'\b(Gran Malecón|Carnaval de Barranquilla)\b',
                r'\b(Teatro Amira de la Rosa|Museo del Caribe)\b',
                r'\b(Río Magdalena|Bocas de Ceniza|Ciénaga)\b'
            ],
            'sports_culture': [
                r'\b(Junior de Barranquilla|Estadio Metropolitano)\b',
                r'\b(Carnaval|Reina del Carnaval|Batalla de Flores)\b',
                r'\b(Vallenato|Cumbia|Mapalé|Gaita)\b'
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

    def _analyze_caribbean_focus(self, content: str, url: str) -> Dict[str, Any]:
        """Analyze Caribbean coast and cultural focus"""
        focus_analysis = {}

        content_lower = content.lower()

        # Caribbean coast indicators
        caribbean_indicators = [
            'caribe', 'costa', 'barranquilla', 'atlántico', 'carnaval',
            'vallenato', 'cumbia', 'magdalena', 'costeño'
        ]

        # Port and commerce indicators
        port_indicators = ['puerto', 'terminal', 'comercio', 'importación', 'exportación', 'fluvial']

        # Cultural indicators
        cultural_indicators = [
            'carnaval', 'reina', 'batalla de flores', 'vallenato', 'cumbia',
            'gaita', 'mapalé', 'tradición', 'folclor'
        ]

        caribbean_count = sum(1 for indicator in caribbean_indicators if indicator in content_lower)
        port_count = sum(1 for indicator in port_indicators if indicator in content_lower)
        cultural_count = sum(1 for indicator in cultural_indicators if indicator in content_lower)

        total_indicators = max(1, caribbean_count + port_count + cultural_count)

        focus_analysis['caribbean_ratio'] = caribbean_count / total_indicators
        focus_analysis['port_ratio'] = port_count / total_indicators
        focus_analysis['cultural_ratio'] = cultural_count / total_indicators

        # Determine primary focus
        if focus_analysis['cultural_ratio'] > 0.4:
            focus_analysis['primary_focus'] = 'cultural'
        elif focus_analysis['port_ratio'] > 0.3:
            focus_analysis['primary_focus'] = 'commerce'
        elif focus_analysis['caribbean_ratio'] > 0.5:
            focus_analysis['primary_focus'] = 'regional'
        else:
            focus_analysis['primary_focus'] = 'general'

        # Carnival content detection
        carnival_terms = ['carnaval', 'reina', 'batalla', 'comparsa', 'disfraz', 'cumbia']
        carnival_count = sum(1 for term in carnival_terms if term in content_lower)
        focus_analysis['carnival_content'] = carnival_count > 1
        focus_analysis['carnival_relevance'] = min(1.0, carnival_count / 6)

        return focus_analysis

    def _calculate_coastal_difficulty(self, text: str) -> float:
        """Calculate difficulty for Caribbean coastal content"""
        if not text:
            return 2.2  # Coastal content tends to be accessible

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Caribbean-specific factors
        local_names = len(re.findall(r'\b[A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)*\b', text))
        coastal_terms = len(re.findall(r'\b(puerto|terminal|fluvial|marítimo|muelle)\b', text, re.IGNORECASE))
        costeño_expressions = len(re.findall(r'\b(chevere|bacano|mamá|papá|mijo|que tal|pues)\b', text, re.IGNORECASE))
        cultural_terms = len(re.findall(r'\b(carnaval|vallenato|cumbia|folclor|tradición)\b', text, re.IGNORECASE))

        # Start with base for coastal content
        difficulty = 2.1

        # Sentence complexity
        if avg_sentence_length > 16:
            difficulty += 0.3
        if avg_sentence_length > 24:
            difficulty += 0.3

        # Word complexity
        if avg_word_length > 6:
            difficulty += 0.2

        # Regional factors
        difficulty += min(0.3, local_names / 70)  # Local names
        difficulty += min(0.3, coastal_terms / 15)  # Port/maritime terminology
        difficulty -= min(0.2, costeño_expressions / 20)  # Coastal expressions (more accessible)
        difficulty += min(0.2, cultural_terms / 25)  # Cultural terms add slight complexity

        return min(5.0, max(1.0, difficulty))

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for Caribbean coastal news"""
        if score < 2.0:
            return 'Principiante'
        elif score < 2.6:
            return 'Intermedio'
        elif score < 3.3:
            return 'Intermedio-Avanzado'
        elif score < 3.9:
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