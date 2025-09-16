"""
La Silla Vacía scraper implementation
Colombia's leading political analysis and investigative journalism platform
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class LaSillaVaciaScraper(SmartScraper):
    """Scraper for La Silla Vacía (lasillavacia.com)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'La Silla Vacía',
            'url': 'https://www.lasillavacia.com',
            'rate_limit': '6/minute'
        }
        super().__init__(config)

        self.sections = [
            'politica',
            'investigacion',
            'poder',
            'congreso',
            'justicia',
            'elecciones',
            'regiones',
            'datos'
        ]

        # CSS selectors for La Silla Vacía's structure
        self.selectors = {
            'article_links': '.article-link, .story-link, '.content-link', .headline-link, h2 a, h3 a',
            'title': 'h1.article-title, h1.story-title, h1.content-title, h1',
            'subtitle': '.article-subtitle, .story-subtitle, .bajada, .dek',
            'content': '.article-content, .story-content, .content-body, '.article-text',
            'author': '.article-author, .story-author, '.byline', .autor',
            'date': '.article-date, .story-date, time, .publish-date',
            'category': '.article-category, .story-category, .section',
            'tags': '.article-tags a, .story-tags a, .tags a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from La Silla Vacía homepage"""
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

        # Get articles from political analysis sections
        for section in self.sections[:5]:  # Focus on core political sections
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
        """Check if URL is a valid La Silla Vacía article"""
        # Political analysis indicators
        article_indicators = [
            '/politica/',
            '/investigacion/',
            '/poder/',
            '/congreso/',
            '/justicia/',
            '/elecciones/',
            '/regiones/',
            '/historia/',
            '/articulo/',
            '/noticia/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/autor/',
            '/tag/',
            '/seccion/',
            '/multimedia/',
            '/video/',
            '/galeria/',
            '/evento/',
            '/directorio/',
            '/quienes-mandan/',
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
        has_id = bool(re.search(r'/\d{4,}', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from La Silla Vacía article"""
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
                if text and len(text) > 30:
                    # Skip promotional content
                    if not self._is_promotional_content(text):
                        content_parts.append(text)

            content = ' '.join(content_parts)

            # Validate content
            if len(content) < 300:
                logger.warning(f"Content too short for {url}")
                return None

            # Extract metadata
            author = self._extract_author(soup)
            published_date = self._extract_date(soup, url)
            category = self._extract_category(soup, url)

            # Political analysis specific features
            entities = self._extract_political_entities(content)
            power_analysis = self._analyze_power_dynamics(content)
            investigation_type = self._classify_investigation_type(content, url)
            difficulty = self._calculate_analysis_difficulty(content)

            # Create document
            doc = ScrapedDocument(
                source=self.source_name,
                source_type='political_analysis',
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                metadata={
                    'category': category,
                    'political_entities': entities,
                    'power_analysis': power_analysis,
                    'investigation_type': investigation_type,
                    'word_count': len(content.split()),
                    'source_focus': 'political_investigation',
                    'target_audience': 'informed_citizens',
                    'analysis_depth': 'deep_investigation'
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Colombia',
                categories=[category] if category else ['política']
            )

            return doc

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    def _is_promotional_content(self, text: str) -> bool:
        """Check if text is promotional content"""
        promo_indicators = [
            'suscríbete',
            'apoya nuestro',
            'donaciones',
            'patrocina',
            'síguenos',
            'boletín',
            'newsletter',
            'fundación gabriel garcía márquez'
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
            '.journalist'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                # Clean prefixes
                author_text = re.sub(r'^(Por:?\s*|Redacción\s*|@)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return author_text

        return "La Silla Vacía"

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
        category_selectors = ['.article-category', '.story-category', '.section']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category and category.lower() not in ['inicio', 'home', 'la silla vacía']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                section_map = {
                    'politica': 'Política',
                    'investigacion': 'Investigación',
                    'poder': 'Poder',
                    'congreso': 'Congreso',
                    'justicia': 'Justicia',
                    'elecciones': 'Elecciones',
                    'regiones': 'Regiones',
                    'datos': 'Datos'
                }
                return section_map.get(section, section.title())

        return 'Política'

    def _extract_political_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract political figures, institutions, and organizations"""
        entities = {}

        patterns = {
            'current_officials': [
                r'\b(Gustavo Petro|Francia Márquez|Luis Gilberto Murillo)\b',
                r'\b(José Antonio Ocampo|Carolina Corcho|Iván Velásquez)\b',
                r'\b(Álvaro Leyva|Patricia Ariza|Aurora Vergara)\b'
            ],
            'former_officials': [
                r'\b(Iván Duque|Marta Lucía Ramírez|Diego Molano)\b',
                r'\b(Juan Manuel Santos|Álvaro Uribe|César Gaviria)\b',
                r'\b(Andrés Pastrana|Ernesto Samper)\b'
            ],
            'political_parties': [
                r'\b(Pacto Histórico|Colombia Humana|Centro Democrático)\b',
                r'\b(Partido Liberal|Partido Conservador|Cambio Radical)\b',
                r'\b(Polo Democrático|Alianza Verde|MAIS)\b'
            ],
            'institutions': [
                r'\b(Presidencia|Casa de Nariño|Vicepresidencia)\b',
                r'\b(Congreso|Senado|Cámara de Representantes)\b',
                r'\b(Fiscalía General|Procuraduría|Contraloría)\b',
                r'\b(Corte Suprema|Corte Constitucional|Consejo de Estado)\b'
            ],
            'electoral_entities': [
                r'\b(CNE|Consejo Nacional Electoral|Registraduría)\b',
                r'\b(MOE|Misión de Observación Electoral)\b'
            ],
            'armed_groups': [
                r'\b(FARC|ELN|Clan del Golfo|AGC|EPL)\b',
                r'\b(disidencias|residuales|grupos armados)\b'
            ],
            'regional_leaders': [
                r'\b(Daniel Quintero|Claudia López|Jorge Iván Ospina)\b',
                r'\b(William Dau|Jaime Pumarejo|Alex Char)\b'
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

    def _analyze_power_dynamics(self, content: str) -> Dict[str, Any]:
        """Analyze power relationships and political dynamics"""
        power_analysis = {}

        content_lower = content.lower()

        # Power indicators
        power_keywords = [
            'poder', 'influencia', 'control', 'dominio', 'hegemonía',
            'alianza', 'coalición', 'pacto', 'acuerdo'
        ]

        # Conflict indicators
        conflict_keywords = [
            'conflicto', 'tensión', 'disputa', 'enfrentamiento',
            'oposición', 'rivalidad', 'confrontación'
        ]

        # Corruption indicators
        corruption_keywords = [
            'corrupción', 'soborno', 'peculado', 'clientelismo',
            'nepotismo', 'tráfico de influencias', 'lavado'
        ]

        # Investigation indicators
        investigation_keywords = [
            'investigación', 'indagación', 'pesquisa', 'seguimiento',
            'fiscalía', 'procuraduría', 'proceso'
        ]

        power_count = sum(1 for keyword in power_keywords if keyword in content_lower)
        conflict_count = sum(1 for keyword in conflict_keywords if keyword in content_lower)
        corruption_count = sum(1 for keyword in corruption_keywords if keyword in content_lower)
        investigation_count = sum(1 for keyword in investigation_keywords if keyword in content_lower)

        total_political = max(1, power_count + conflict_count + corruption_count + investigation_count)

        power_analysis['power_focus'] = power_count / total_political
        power_analysis['conflict_focus'] = conflict_count / total_political
        power_analysis['corruption_focus'] = corruption_count / total_political
        power_analysis['investigation_focus'] = investigation_count / total_political

        # Determine primary theme
        max_focus = max(power_analysis.values())
        if power_analysis['corruption_focus'] == max_focus and max_focus > 0.3:
            power_analysis['primary_theme'] = 'corruption'
        elif power_analysis['investigation_focus'] == max_focus and max_focus > 0.3:
            power_analysis['primary_theme'] = 'investigation'
        elif power_analysis['conflict_focus'] == max_focus and max_focus > 0.3:
            power_analysis['primary_theme'] = 'political_conflict'
        elif power_analysis['power_focus'] == max_focus and max_focus > 0.3:
            power_analysis['primary_theme'] = 'power_analysis'
        else:
            power_analysis['primary_theme'] = 'general_politics'

        return power_analysis

    def _classify_investigation_type(self, content: str, url: str) -> str:
        """Classify the type of investigative content"""
        content_lower = content.lower()

        # Data journalism
        data_indicators = ['datos', 'estadística', 'cifras', 'gráfico', 'análisis cuantitativo']
        if any(indicator in content_lower for indicator in data_indicators) or '/datos/' in url:
            return 'data_journalism'

        # Corruption investigation
        corruption_indicators = ['corrupción', 'soborno', 'peculado', 'lavado', 'malversación']
        if any(indicator in content_lower for indicator in corruption_indicators):
            return 'corruption_investigation'

        # Power mapping
        power_indicators = ['redes', 'conexiones', 'influencia', 'poder', 'mapa político']
        if any(indicator in content_lower for indicator in power_indicators) or '/poder/' in url:
            return 'power_mapping'

        # Electoral analysis
        electoral_indicators = ['elecciones', 'voto', 'candidato', 'campaña', 'electoral']
        if any(indicator in content_lower for indicator in electoral_indicators) or '/elecciones/' in url:
            return 'electoral_analysis'

        # Congressional tracking
        congress_indicators = ['congreso', 'senado', 'cámara', 'legislativo', 'proyecto de ley']
        if any(indicator in content_lower for indicator in congress_indicators) or '/congreso/' in url:
            return 'congressional_tracking'

        # Regional politics
        regional_indicators = ['región', 'territorial', 'local', 'departamento', 'municipio']
        if any(indicator in content_lower for indicator in regional_indicators) or '/regiones/' in url:
            return 'regional_politics'

        return 'political_analysis'

    def _calculate_analysis_difficulty(self, text: str) -> float:
        """Calculate difficulty for political analysis content"""
        if not text:
            return 4.2  # Political analysis is typically complex

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Political complexity factors
        political_jargon = len(re.findall(r'\b(institucionalidad|gobernanza|democracia|constitucionalidad)\b', text, re.IGNORECASE))
        legal_terms = len(re.findall(r'\b(jurisprudencia|normativa|reglamentación|decreto|resolución)\b', text, re.IGNORECASE))
        complex_analysis = len(re.findall(r'\b(correlación|causalidad|sistémico|estructural|coyuntural)\b', text, re.IGNORECASE))
        proper_names = len(re.findall(r'\b[A-Z][a-záéíóúñ]+\s+[A-Z][a-záéíóúñ]+\b', text))

        # Start high for political analysis
        difficulty = 4.0

        # Sentence complexity
        if avg_sentence_length > 25:
            difficulty += 0.3
        if avg_sentence_length > 35:
            difficulty += 0.4

        # Word complexity
        if avg_word_length > 7:
            difficulty += 0.3

        # Political analysis complexity
        difficulty += min(0.7, political_jargon / 20)
        difficulty += min(0.5, legal_terms / 15)
        difficulty += min(0.6, complex_analysis / 10)
        difficulty += min(0.3, proper_names / 50)  # Many names can complicate reading

        return min(5.0, difficulty)

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for political analysis"""
        if score < 3.8:
            return 'Intermedio-Avanzado'
        elif score < 4.3:
            return 'Avanzado'
        elif score < 4.8:
            return 'Avanzado-Experto'
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