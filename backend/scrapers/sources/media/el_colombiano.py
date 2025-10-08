"""
El Colombiano newspaper scraper implementation
Medellín's leading newspaper and Antioquia regional news source
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class ElColombianoScraper(SmartScraper):
    """Scraper for El Colombiano (elcolombiano.com)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'El Colombiano',
            'url': 'https://www.elcolombiano.com',
            'rate_limit': '10/minute'
        }
        super().__init__(config)

        self.sections = [
            'antioquia',
            'medellin',
            'colombia',
            'politica',
            'economia',
            'internacional',
            'deportes',
            'cultura',
            'tecnologia'
        ]

        # CSS selectors for El Colombiano's structure
        self.selectors = {
            'article_links': '.article-link, .story-link, .card-link, .headline-link, h2 a, h3 a',
            'title': 'h1.article-title, h1.story-title, h1.headline, h1',
            'subtitle': '.article-subtitle, .story-subtitle, .bajada, .entradilla',
            'content': '.article-content, .story-content, .content-body, .texto-noticia',
            'author': '.article-author, .story-author, .byline, .autor',
            'date': '.article-date, .story-date, time, .fecha',
            'category': '.article-category, .story-category, .seccion',
            'tags': '.article-tags a, .story-tags a, .etiquetas a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from El Colombiano homepage"""
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

        # Get articles from regional sections
        for section in self.sections[:6]:  # Focus on regional and key sections
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
        """Check if URL is a valid El Colombiano article"""
        # Article indicators
        article_indicators = [
            '/antioquia/',
            '/medellin/',
            '/colombia/',
            '/politica/',
            '/economia/',
            '/internacional/',
            '/deportes/',
            '/cultura/',
            '/tecnologia/',
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
            '/blog/',
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
        """Extract content from El Colombiano article"""
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

            # Regional-specific analysis
            entities = self._extract_antioquia_entities(content)
            regional_focus = self._analyze_regional_focus(content, url)
            difficulty = self._calculate_regional_difficulty(content)

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
                    'antioquia_entities': entities,
                    'regional_focus': regional_focus,
                    'word_count': len(content.split()),
                    'region': 'Antioquia',
                    'city_focus': 'Medellín',
                    'local_relevance': True
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Antioquia',
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
            'publicidad'
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

        return "El Colombiano"

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
                if category and category.lower() not in ['inicio', 'home', 'el colombiano']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                section_map = {
                    'antioquia': 'Antioquia',
                    'medellin': 'Medellín',
                    'colombia': 'Nacional',
                    'politica': 'Política',
                    'economia': 'Economía',
                    'internacional': 'Internacional',
                    'deportes': 'Deportes',
                    'cultura': 'Cultura',
                    'tecnologia': 'Tecnología'
                }
                return section_map.get(section, section.title())

        return 'Regional'

    def _extract_antioquia_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Antioquia and Medellín specific entities"""
        entities = {}

        patterns = {
            'local_politicians': [
                r'\b(Daniel Quintero|Federico Gutiérrez|Aníbal Gaviria)\b',
                r'\b(Luis Pérez|Sergio Fajardo|Alonso Salazar)\b',
                r'\b(Juan Gómez Martínez|Eugenio Prieto)\b'
            ],
            'local_institutions': [
                r'\b(Alcaldía de Medellín|Gobernación de Antioquia)\b',
                r'\b(Concejo de Medellín|Asamblea de Antioquia)\b',
                r'\b(EPM|Área Metropolitana|Metro de Medellín)\b',
                r'\b(UdeA|Universidad de Antioquia|EAFIT|UPB)\b'
            ],
            'municipalities': [
                r'\b(Medellín|Bello|Itagüí|Envigado|Sabaneta)\b',
                r'\b(La Estrella|Caldas|Copacabana|Girardota)\b',
                r'\b(Rionegro|Marinilla|Guarne|El Carmen)\b',
                r'\b(Turbo|Apartadó|Caucasia|Puerto Berrío)\b'
            ],
            'neighborhoods_zones': [
                r'\b(El Poblado|Laureles|Belén|La América)\b',
                r'\b(Envigado|Sabaneta|Comuna 13|Comuna 1)\b',
                r'\b(Centro|La Candelaria|Boston|Estadio)\b'
            ],
            'companies_organizations': [
                r'\b(EPM|Grupo Éxito|Bancolombia|Grupo Sura)\b',
                r'\b(Nutresa|Corona|Argos|Celsia)\b',
                r'\b(Comfama|Comfenalco|Proantioquia)\b'
            ],
            'infrastructure_transport': [
                r'\b(Metro|Metrocable|Tranvía|BRT)\b',
                r'\b(Aeropuerto José María Córdova|Olaya Herrera)\b',
                r'\b(Túnel de Oriente|Autopista Norte|Vía al Mar)\b'
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

    def _analyze_regional_focus(self, content: str, url: str) -> Dict[str, Any]:
        """Analyze regional focus of the content"""
        focus_analysis = {}

        content_lower = content.lower()

        # Local vs national focus
        local_indicators = ['medellín', 'antioquia', 'paisa', 'valle de aburrá', 'oriente antioqueño']
        national_indicators = ['colombia', 'país', 'nacional', 'bogotá', 'presidencia']

        local_count = sum(1 for indicator in local_indicators if indicator in content_lower)
        national_count = sum(1 for indicator in national_indicators if indicator in content_lower)

        total_indicators = max(1, local_count + national_count)
        focus_analysis['local_ratio'] = local_count / total_indicators
        focus_analysis['national_ratio'] = national_count / total_indicators

        # Determine primary focus
        if focus_analysis['local_ratio'] > 0.6:
            focus_analysis['primary_focus'] = 'local'
        elif focus_analysis['national_ratio'] > 0.6:
            focus_analysis['primary_focus'] = 'national'
        else:
            focus_analysis['primary_focus'] = 'mixed'

        # Regional relevance score
        regional_terms = ['alcalde', 'gobernador', 'concejo', 'asamblea', 'municipio', 'comuna']
        regional_count = sum(1 for term in regional_terms if term in content_lower)
        focus_analysis['regional_relevance'] = min(1.0, regional_count / 10)

        return focus_analysis

    def _calculate_regional_difficulty(self, text: str) -> float:
        """Calculate difficulty for regional news content"""
        if not text:
            return 2.5  # Regional news is typically accessible

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Regional-specific factors
        local_names = len(re.findall(r'\b[A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)*\b', text))
        administrative_terms = len(re.findall(r'\b(alcaldía|gobernación|secretaría|concejo|asamblea)\b', text, re.IGNORECASE))
        paisa_expressions = len(re.findall(r'\b(pues|entonces|muy|hijuemadre|parcero|mijo)\b', text, re.IGNORECASE))

        # Start with base for regional content
        difficulty = 2.4

        # Sentence complexity
        if avg_sentence_length > 16:
            difficulty += 0.3
        if avg_sentence_length > 24:
            difficulty += 0.3

        # Word complexity
        if avg_word_length > 6:
            difficulty += 0.2

        # Regional factors
        difficulty += min(0.4, local_names / 100)  # Many local names add complexity
        difficulty += min(0.3, administrative_terms / 20)  # Administrative language
        difficulty -= min(0.2, paisa_expressions / 30)  # Paisa expressions make it more accessible

        return min(5.0, max(1.0, difficulty))

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for regional news"""
        if score < 2.2:
            return 'Principiante'
        elif score < 2.9:
            return 'Intermedio'
        elif score < 3.6:
            return 'Intermedio-Avanzado'
        elif score < 4.2:
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