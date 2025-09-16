"""
Portafolio business newspaper scraper implementation
Colombia's leading financial and business news source (El Tiempo Group)
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class PortafolioScraper(SmartScraper):
    """Scraper for Portafolio (portafolio.co)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'Portafolio',
            'url': 'https://www.portafolio.co',
            'rate_limit': '10/minute'
        }
        super().__init__(config)

        self.sections = [
            'economia',
            'negocios',
            'finanzas',
            'mis-finanzas',
            'empresas',
            'internacional',
            'tendencias',
            'innovacion',
            'opinion'
        ]

        # CSS selectors for Portafolio's structure (similar to El Tiempo)
        self.selectors = {
            'article_links': '.articulo-link, .card-link, .story-link, h2 a, h3 a, .headline a',
            'title': 'h1.titulo, h1.headline, h1.article-title, h1',
            'subtitle': 'h2.sumario, .bajada, .dek, .article-subtitle',
            'content': '.articulo-contenido, .article-body, .content-body, .story-body',
            'author': '.autor-nombre, .byline, .author-name, .autor',
            'date': '.fecha, time, .article-date, .publish-date',
            'category': '.categoria, .section-name, .breadcrumb-item',
            'tags': '.tags a, .article-tags a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from Portafolio homepage"""
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
        """Check if URL is a valid Portafolio article"""
        # Business article indicators
        article_indicators = [
            '/economia/',
            '/negocios/',
            '/finanzas/',
            '/mis-finanzas/',
            '/empresas/',
            '/internacional/',
            '/tendencias/',
            '/innovacion/',
            '/analisis/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/tema/',
            '/autor/',
            '/seccion/',
            '/multimedia/',
            '/video/',
            '/podcast/',
            '/galeria/',
            '/calculadoras/',
            '/mercados/',
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
        has_id = bool(re.search(r'/\d{6,}', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from Portafolio article"""
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
                    # Skip promotional and advertising content
                    if not self._is_promotional_content(text):
                        content_parts.append(text)

            content = ' '.join(content_parts)

            # Validate content
            if len(content) < 250:
                logger.warning(f"Content too short for {url}")
                return None

            # Check for paywall
            if self._is_paywall_content(content):
                logger.info(f"Paywall detected for {url}")

            # Extract metadata
            author = self._extract_author(soup)
            published_date = self._extract_date(soup, url)
            category = self._extract_category(soup, url)

            # Business-specific analysis
            entities = self._extract_business_entities(content)
            market_data = self._extract_market_data(content)
            difficulty = self._calculate_financial_difficulty(content)

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
                    'market_data': market_data,
                    'word_count': len(content.split()),
                    'source_focus': 'finance_business',
                    'target_audience': 'business_professionals',
                    'parent_group': 'Casa Editorial El Tiempo'
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Colombia',
                categories=[category] if category else ['finanzas']
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
            'boletín',
            'newsletter',
            'descarga la app',
            'síguenos',
            'invierta en',
            'oferta especial'
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
            'contenido premium',
            'lee la nota completa'
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in paywall_indicators)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        author_selectors = [
            '.autor-nombre',
            '.byline',
            '.author-name',
            '.autor',
            '.redaccion-portafolio'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                # Clean prefixes
                author_text = re.sub(r'^(Por:?\s*|Redacción\s*|@)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return author_text

        return "Portafolio"

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
        date_selectors = ['.fecha', '.article-date', '.publish-date']
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
        category_selectors = ['.categoria', '.section-name', '.breadcrumb-item']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category and category.lower() not in ['inicio', 'home', 'portafolio']:
                    return category

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url.lower():
                section_map = {
                    'mis-finanzas': 'Finanzas Personales',
                    'negocios': 'Negocios',
                    'economia': 'Economía',
                    'finanzas': 'Finanzas',
                    'empresas': 'Empresas',
                    'internacional': 'Internacional',
                    'tendencias': 'Tendencias',
                    'innovacion': 'Innovación'
                }
                return section_map.get(section, section.title())

        return 'Finanzas'

    def _extract_business_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract business and financial entities"""
        entities = {}

        patterns = {
            'colombian_companies': [
                r'\b(Ecopetrol|Bancolombia|Grupo Éxito|EPM|ETB|Avianca)\b',
                r'\b(Bavaria|Alpina|Nutresa|Cemex|Corona|Argos)\b',
                r'\b(Terpel|Claro|Movistar|Une|DirecTV|ISA)\b',
                r'\b(Interconexión Eléctrica|Grupo Sura|Grupo Bolívar)\b'
            ],
            'financial_entities': [
                r'\b(Banco de la República|BBVA Colombia|Davivienda)\b',
                r'\b(Banco de Bogotá|Banco Popular|Colpatria)\b',
                r'\b(Superfinanciera|BVC|Deceval|Credicorp Capital)\b'
            ],
            'government_economic': [
                r'\b(MinHacienda|MinComercio|DANE|DNP|DIAN)\b',
                r'\b(Procolombia|Bancóldex|Finagro|FDN)\b',
                r'\b(Superintendencia Financiera|SIC)\b'
            ],
            'international_markets': [
                r'\b(NYSE|NASDAQ|Dow Jones|S&P 500)\b',
                r'\b(WTI|Brent|oro|cobre|café)\b',
                r'\b(Fed|BCE|Reserva Federal|FMI)\b'
            ],
            'currencies_commodities': [
                r'\b(dólar|euro|peso|TRM|UVR)\b',
                r'\b(petróleo|café|carbón|oro|níquel)\b',
                r'\b(bitcoin|ethereum|criptomoneda)\b'
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

    def _extract_market_data(self, text: str) -> Dict[str, List[str]]:
        """Extract market data and financial metrics"""
        market_data = {}

        patterns = {
            'stock_prices': [
                r'\$\s*\d+[.,]?\d*',
                r'\d+[.,]?\d*\s*pesos',
                r'precio.*\$\s*\d+[.,]?\d*'
            ],
            'percentages': [
                r'\d+[.,]?\d*\s*%',
                r'\d+[.,]?\d*\s*por\s*ciento'
            ],
            'financial_ratios': [
                r'\b(ROE|ROA|EBITDA|P/E|PER)\b',
                r'\b(margen|rentabilidad|utilidad)\b'
            ],
            'economic_indicators': [
                r'\b(PIB|inflación|desempleo|IPC|DTF|TRM)\b',
                r'\b(tasa de interés|tasa de cambio|devaluación)\b'
            ],
            'market_movements': [
                r'\b(sube|baja|aumenta|disminuye|crece)\b.*\d+[.,]?\d*\s*%',
                r'\b(ganancia|pérdida).*\$\s*\d+[.,]?\d*'
            ]
        }

        for data_type, pattern_list in patterns.items():
            found = set()
            for pattern in pattern_list:
                matches = re.findall(pattern, text, re.IGNORECASE)
                found.update(matches)
            if found:
                market_data[data_type] = list(found)

        return market_data

    def _calculate_financial_difficulty(self, text: str) -> float:
        """Calculate difficulty for financial content"""
        if not text:
            return 3.8  # Financial content is typically complex

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Financial complexity indicators
        financial_jargon = len(re.findall(r'\b(liquidez|solvencia|rentabilidad|volatilidad|diversificación|derivados|hedge)\b', text, re.IGNORECASE))
        numbers_data = len(re.findall(r'\d+[.,]?\d*\s*%|\$\s*\d+|USD\s*\d+|COP\s*\d+', text))
        acronyms = len(re.findall(r'\b[A-Z]{2,}\b', text))

        # Start higher for financial content
        difficulty = 3.5

        if avg_sentence_length > 20:
            difficulty += 0.3
        if avg_sentence_length > 30:
            difficulty += 0.4

        if avg_word_length > 7:
            difficulty += 0.3

        # Financial complexity factors
        difficulty += min(1.0, financial_jargon / 40)
        difficulty += min(0.6, numbers_data / 80)
        difficulty += min(0.4, acronyms / 25)

        return min(5.0, difficulty)

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for financial content"""
        if score < 3.2:
            return 'Intermedio'
        elif score < 4.0:
            return 'Intermedio-Avanzado'
        elif score < 4.6:
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