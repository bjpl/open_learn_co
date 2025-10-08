"""
La República business newspaper scraper implementation
Colombia's leading business and financial news source
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class LaRepublicaScraper(SmartScraper):
    """Scraper for La República (larepublica.co)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'La República',
            'url': 'https://www.larepublica.co',
            'rate_limit': '12/minute'
        }
        super().__init__(config)

        self.sections = [
            'economia',
            'empresas',
            'finanzas',
            'globoeconomia',
            'consumo',
            'infraestructura',
            'opinion',
            'especiales'
        ]

        # CSS selectors for La República's structure
        self.selectors = {
            'article_links': '.story-link, .article-link, .card-link, h2 a, h3 a, .headline a',
            'title': 'h1.story-title, h1.article-title, h1.headline, h1',
            'subtitle': '.story-subtitle, .article-subtitle, .bajada, .dek',
            'content': '.story-body, .article-body, .content-body, .story-text',
            'author': '.story-author, .article-author, .byline, .author',
            'date': '.story-date, .article-date, time, .publish-date',
            'category': '.story-category, .article-category, .section',
            'tags': '.story-tags a, .article-tags a, .tags a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from La República homepage"""
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

        # Get articles from business sections
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
        """Check if URL is a valid La República article"""
        # Business article indicators
        article_indicators = [
            '/economia/',
            '/empresas/',
            '/finanzas/',
            '/globoeconomia/',
            '/consumo/',
            '/infraestructura/',
            '/especiales/',
            '/analisis/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/autor/',
            '/tag/',
            '/seccion/',
            '/multimedia/',
            '/video/',
            '/podcast/',
            '/galeria/',
            '/mercados-en-vivo/',
            '#',
            'mailto:',
            'javascript:',
            '.pdf',
            '.jpg',
            '.png',
            'twitter.com',
            'facebook.com',
            'linkedin.com'
        ]

        # Check indicators
        has_indicator = any(indicator in url.lower() for indicator in article_indicators)

        # Check exclusions
        should_exclude = any(pattern in url.lower() for pattern in exclude_patterns)

        # Check for article ID pattern
        has_id = bool(re.search(r'/\d{6,}/', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from La República article"""
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

            # Business-specific analysis
            entities = self._extract_business_entities(content)
            economic_indicators = self._extract_economic_indicators(content)
            difficulty = self._calculate_business_difficulty(content)

            # Create document
            doc = ScrapedDocument(
                source=self.source_name,
                source_type='business_newspaper',
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                metadata={
                    'category': category,
                    'business_entities': entities,
                    'economic_indicators': economic_indicators,
                    'word_count': len(content.split()),
                    'source_focus': 'business',
                    'target_audience': 'professionals'
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Colombia',
                categories=[category] if category else ['economía']
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
            'contenido patrocinado',
            'publicidad',
            'síguenos',
            'descarga',
            'boletín',
            'newsletter'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in promo_indicators)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        author_selectors = [
            '.story-author',
            '.article-author',
            '.byline',
            '.author',
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

        return "La República"

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
        date_selectors = ['.story-date', '.article-date', '.publish-date', '.fecha']
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
        category_selectors = ['.story-category', '.article-category', '.section']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category and category.lower() not in ['inicio', 'home', 'la república']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                return section.replace('-', ' ').title()

        return 'Economía'

    def _extract_business_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract business and economic entities"""
        entities = {}

        patterns = {
            'companies': [
                r'\b(Ecopetrol|Bancolombia|Grupo Éxito|EPM|ETB|Avianca)\b',
                r'\b(Bavaria|Alpina|Nutresa|Cemex|Corona|Argos)\b',
                r'\b(Terpel|Claro|Movistar|Une|DirecTV)\b'
            ],
            'financial_institutions': [
                r'\b(Banco de la República|BBVA|Davivienda|Colpatria)\b',
                r'\b(Bancolombia|Banco de Bogotá|Banco Popular)\b',
                r'\b(Superfinanciera|Fogafín|Banca de Inversión)\b'
            ],
            'government_entities': [
                r'\b(MinHacienda|MinComercio|DANE|DNP|DIAN)\b',
                r'\b(Banco de la República|Superfinanciera|SIC)\b',
                r'\b(Procolombia|Bancóldex|Finagro)\b'
            ],
            'economic_sectors': [
                r'\b(petróleo|café|carbón|oro|banano|flores)\b',
                r'\b(manufactura|construcción|servicios|comercio)\b',
                r'\b(telecomunicaciones|energía|transporte|turismo)\b'
            ],
            'international_entities': [
                r'\b(FMI|Banco Mundial|BID|CAF|OCDE)\b',
                r'\b(Fed|BCE|Reserva Federal)\b'
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

    def _extract_economic_indicators(self, text: str) -> Dict[str, List[str]]:
        """Extract economic indicators and metrics"""
        indicators = {}

        patterns = {
            'currencies': [
                r'\b(peso|dólar|euro|yuan|yen)\b',
                r'\$\s*\d+[.,]?\d*\s*(millones?|billones?|mil)?',
                r'\d+[.,]?\d*\s*pesos'
            ],
            'percentages': [
                r'\d+[.,]?\d*\s*%',
                r'\d+[.,]?\d*\s*por\s*ciento'
            ],
            'financial_metrics': [
                r'\b(PIB|inflación|desempleo|IPC|DTF|TRM)\b',
                r'\b(ganancias|utilidades|ingresos|ventas|EBITDA)\b',
                r'\b(capitalización|valoración|acciones|bonos)\b'
            ],
            'market_terms': [
                r'\b(mercado|bolsa|inversión|crédito|liquidez)\b',
                r'\b(riesgo|volatilidad|rendimiento|dividendos)\b'
            ]
        }

        for indicator_type, pattern_list in patterns.items():
            found = set()
            for pattern in pattern_list:
                matches = re.findall(pattern, text, re.IGNORECASE)
                found.update(matches)
            if found:
                indicators[indicator_type] = list(found)

        return indicators

    def _calculate_business_difficulty(self, text: str) -> float:
        """Calculate difficulty specifically for business content"""
        if not text:
            return 3.5  # Business content is typically more complex

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Business-specific complexity indicators
        financial_terms = len(re.findall(r'\b(capitalización|amortización|liquidez|volatilidad|rentabilidad|derivados)\b', text, re.IGNORECASE))
        numbers_and_percentages = len(re.findall(r'\d+[.,]?\d*\s*%|\$\s*\d+|USD\s*\d+', text))
        technical_acronyms = len(re.findall(r'\b[A-Z]{2,}\b', text))

        # Start with higher base for business content
        difficulty = 3.0

        if avg_sentence_length > 18:
            difficulty += 0.4
        if avg_sentence_length > 25:
            difficulty += 0.4

        if avg_word_length > 6.5:
            difficulty += 0.3

        # Business complexity factors
        difficulty += min(0.8, financial_terms / 50)
        difficulty += min(0.5, numbers_and_percentages / 100)
        difficulty += min(0.4, technical_acronyms / 30)

        return min(5.0, difficulty)

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for business content"""
        if score < 3.0:
            return 'Intermedio'
        elif score < 3.8:
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
                    if '/' in pattern:  # Numeric format
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    elif '-' in pattern:  # ISO format
                        year, month, day = match.groups()
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

        # Remove extra whitespace
        text = ' '.join(text.split())
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()