"""
La FM radio news scraper implementation
RCN Radio's news and opinion station
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class LaFMScraper(SmartScraper):
    """Scraper for La FM (lafm.com.co)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'La FM',
            'url': 'https://www.lafm.com.co',
            'rate_limit': '15/minute'
        }
        super().__init__(config)

        self.sections = [
            'colombia',
            'politica',
            'internacional',
            'judicial',
            'bogota',
            'antioquia',
            'deportes',
            'economia',
            'tecnologia'
        ]

        # CSS selectors for La FM's structure
        self.selectors = {
            'article_links': '.noticia-link, .article-link, .card-link, h2 a, h3 a, .story-link',
            'title': 'h1.noticia-title, h1.article-title, h1.title, h1',
            'subtitle': '.noticia-subtitle, .article-subtitle, .bajada, .lead',
            'content': '.noticia-content, .article-content, .content-body, .story-body',
            'author': '.noticia-author, .article-author, .author, .byline',
            'date': '.noticia-date, .article-date, time, .publish-date',
            'category': '.noticia-category, .article-category, .section',
            'tags': '.noticia-tags a, .article-tags a, .tags a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from La FM homepage"""
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

        # Get articles from news sections
        for section in self.sections[:5]:  # Limit requests
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
        """Check if URL is a valid La FM article"""
        # News article indicators
        article_indicators = [
            '/colombia/',
            '/politica/',
            '/internacional/',
            '/judicial/',
            '/bogota/',
            '/antioquia/',
            '/deportes/',
            '/economia/',
            '/tecnologia/',
            '/noticia/',
            '/articulo/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/programa/',
            '/emisora/',
            '/audio/',
            '/podcast/',
            '/multimedia/',
            '/video/',
            '/galeria/',
            '/opinion/',
            '/tag/',
            '/autor/',
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
            'instagram.com'
        ]

        # Check indicators
        has_indicator = any(indicator in url.lower() for indicator in article_indicators)

        # Check exclusions
        should_exclude = any(pattern in url.lower() for pattern in exclude_patterns)

        # Check for article ID pattern
        has_id = bool(re.search(r'/\d{4,}', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from La FM article"""
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
                if text and len(text) > 20:
                    # Skip radio-specific promotional content
                    if not self._is_radio_promotional_content(text):
                        content_parts.append(text)

            content = ' '.join(content_parts)

            # Validate content
            if len(content) < 150:
                logger.warning(f"Content too short for {url}")
                return None

            # Extract metadata
            author = self._extract_author(soup)
            published_date = self._extract_date(soup, url)
            category = self._extract_category(soup, url)

            # Radio news specific analysis
            entities = self._extract_news_entities(content)
            audio_references = self._extract_audio_references(content, soup)
            difficulty = self._calculate_news_difficulty(content)

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
                    'news_entities': entities,
                    'audio_references': audio_references,
                    'word_count': len(content.split()),
                    'source_type': 'radio',
                    'media_group': 'RCN',
                    'content_style': 'conversational'
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
            'transmisión',
            'podcast',
            'audio completo',
            'síguenos en redes'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in radio_promo_indicators)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        author_selectors = [
            '.noticia-author',
            '.article-author',
            '.author',
            '.byline',
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

        return "La FM"

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
        date_selectors = ['.noticia-date', '.article-date', '.publish-date', '.fecha']
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
        category_selectors = ['.noticia-category', '.article-category', '.section']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category and category.lower() not in ['inicio', 'home', 'la fm']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                section_map = {
                    'colombia': 'Nacional',
                    'politica': 'Política',
                    'internacional': 'Internacional',
                    'judicial': 'Judicial',
                    'bogota': 'Bogotá',
                    'antioquia': 'Antioquia',
                    'deportes': 'Deportes',
                    'economia': 'Economía',
                    'tecnologia': 'Tecnología'
                }
                return section_map.get(section, section.title())

        return 'Noticias'

    def _extract_news_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract news-relevant entities"""
        entities = {}

        patterns = {
            'political_figures': [
                r'\b(Gustavo Petro|Francia Márquez|Iván Duque|Álvaro Uribe)\b',
                r'\b(Juan Manuel Santos|César Gaviria|Andrés Pastrana)\b',
                r'\b(Sergio Fajardo|Rodolfo Hernández|Federico Gutiérrez)\b'
            ],
            'government_institutions': [
                r'\b(Presidencia|Casa de Nariño|Congreso|Senado|Cámara)\b',
                r'\b(Fiscalía|Procuraduría|Contraloría|CNE|Registraduría)\b',
                r'\b(Corte Suprema|Corte Constitucional|Consejo de Estado)\b',
                r'\b(Policía Nacional|Ejército|Armada|Fuerza Aérea)\b'
            ],
            'armed_groups': [
                r'\b(FARC|ELN|Clan del Golfo|AGC|EPL)\b',
                r'\b(disidencias|residuales|grupos armados)\b'
            ],
            'cities_regions': [
                r'\b(Bogotá|Medellín|Cali|Barranquilla|Cartagena|Cúcuta)\b',
                r'\b(Bucaramanga|Pereira|Manizales|Armenia|Ibagué)\b',
                r'\b(Antioquia|Valle|Cundinamarca|Atlántico|Santander)\b',
                r'\b(Chocó|Nariño|Cauca|Norte de Santander|Arauca)\b'
            ],
            'international_entities': [
                r'\b(Estados Unidos|Venezuela|Ecuador|Brasil|México)\b',
                r'\b(ONU|OEA|CELAC|UNASUR|Mercosur)\b',
                r'\b(Biden|Maduro|Lasso)\b'
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

    def _extract_audio_references(self, text: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract audio-related content references"""
        audio_refs = {}

        # Look for audio elements in the page
        audio_elements = soup.find_all(['audio', 'iframe'])
        audio_refs['has_audio'] = len(audio_elements) > 0
        audio_refs['audio_count'] = len(audio_elements)

        # Look for interview indicators in text
        interview_indicators = [
            r'\b(entrevista|conversación|diálogo)\b',
            r'\b(dijo|declaró|afirmó|comentó)\b.*en.*La FM',
            r'\b(en diálogo con|habló con|conversó con)\b'
        ]

        interview_matches = []
        for indicator in interview_indicators:
            matches = re.findall(indicator, text, re.IGNORECASE)
            interview_matches.extend(matches)

        audio_refs['interview_indicators'] = interview_matches
        audio_refs['likely_interview'] = len(interview_matches) > 2

        # Look for program references
        program_mentions = re.findall(r'\b(programa|emisión|transmisión|en vivo)\b', text, re.IGNORECASE)
        audio_refs['program_mentions'] = len(program_mentions)

        return audio_refs

    def _calculate_news_difficulty(self, text: str) -> float:
        """Calculate difficulty for radio news content"""
        if not text:
            return 2.5  # Radio news is typically more accessible

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Radio-specific factors (more conversational)
        conversational_indicators = len(re.findall(r'\b(dijo|comentó|explicó|señaló|manifestó)\b', text, re.IGNORECASE))
        complex_terms = len(re.findall(r'\b\w{10,}\b', text))
        technical_language = len(re.findall(r'\b(constitucional|jurídico|normatividad|reglamentación)\b', text, re.IGNORECASE))

        # Start lower for radio content (more accessible)
        difficulty = 2.0

        if avg_sentence_length > 15:
            difficulty += 0.3
        if avg_sentence_length > 25:
            difficulty += 0.4

        if avg_word_length > 6:
            difficulty += 0.2

        # Adjust for conversational nature
        difficulty -= min(0.5, conversational_indicators / 50)  # More conversational = easier

        # Add for complexity
        difficulty += min(0.6, complex_terms / 100)
        difficulty += min(0.5, technical_language / 30)

        return min(5.0, max(1.0, difficulty))

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for radio news"""
        if score < 2.0:
            return 'Principiante'
        elif score < 2.8:
            return 'Intermedio'
        elif score < 3.5:
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
            r'(\d{4})-(\d{2})-(\d{2})',                # "2024-01-15"
            r'Hace\s+(\d+)\s+(hora|día|minuto)s?'       # "Hace 2 horas"
        ]

        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if 'Hace' in pattern:
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