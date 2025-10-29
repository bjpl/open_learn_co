"""
Portafolio business newspaper scraper implementation
Colombia's leading financial and business news source (El Tiempo Group)
"""

import re
from typing import Any, Dict, List, Optional
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

        # Updated CSS selectors based on actual Portafolio.co HTML structure
        self.selectors = {
            'article_links': 'article a, .article-top a, .listing_main a, .listing_secondary a, h2 a, h3 a, h4 a',
            'title': 'h1[itemprop="headline"], h1.title, h1',
            'subtitle': 'h2[itemprop="description"], .summary, .excerpt, .lead, .bajada, p[itemprop="description"]',
            'content': '#articulocontenido, div[itemprop="articleBody"], .article-body, .content-body, .story-content',
            'author': 'span[itemprop="author"], a[itemprop="author"], .author-name, .byline, .firma, .autor-nombre',
            'date': 'time[itemprop="datePublished"], time[datetime], time, .publish-date, .date, .fecha',
            'category': '.breadcrumb a, nav[aria-label="breadcrumb"] a, .section-name, .categoria',
            'tags': '.tags a, .keywords a, .article-tags a'
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
        """Extract content from Portafolio article with improved error handling"""
        soup = self.parse_html(article_html)

        try:
            # Extract title with fallback options
            title_elem = soup.select_one(self.selectors['title'])
            if not title_elem:
                # Fallback: try meta tags
                title_meta = soup.find('meta', property='og:title')
                if title_meta and title_meta.get('content'):
                    title = self._clean_text(title_meta.get('content'))
                else:
                    logger.warning(f"No title found for {url}")
                    return None
            else:
                title = self._clean_text(title_elem.get_text())

            if not title or len(title) < 10:
                logger.warning(f"Title too short or empty for {url}")
                return None

            # Extract subtitle with multiple fallback options
            subtitle = ""
            subtitle_elem = soup.select_one(self.selectors['subtitle'])
            if subtitle_elem:
                subtitle = self._clean_text(subtitle_elem.get_text())
            else:
                # Fallback to meta description
                desc_meta = soup.find('meta', property='og:description')
                if desc_meta and desc_meta.get('content'):
                    subtitle = self._clean_text(desc_meta.get('content'))

            # Extract content with improved selector logic
            content_elem = soup.select_one(self.selectors['content'])
            if not content_elem:
                # Fallback: try to find main article container
                content_elem = soup.find('article') or soup.find('main')
                if not content_elem:
                    logger.warning(f"No content container found for {url}")
                    return None

            # Process content with better filtering
            content_parts = []
            if subtitle and len(subtitle) > 20:
                content_parts.append(subtitle)

            # Extract paragraphs more selectively
            paragraphs = content_elem.find_all('p')
            logger.debug(f"Found {len(paragraphs)} paragraphs in content element")

            for p in paragraphs:
                # Skip if paragraph contains script, style, or nested elements
                if p.find(['script', 'style', 'noscript']):
                    continue

                text = self._clean_text(p.get_text())

                # More strict filtering
                if text and len(text) > 30:
                    # Skip promotional, advertising, and navigation content
                    if not self._is_promotional_content(text) and not self._is_navigation_text(text):
                        content_parts.append(text)

            content = ' '.join(content_parts)

            # Validate content (reduced threshold for Portafolio which has shorter articles)
            logger.debug(f"Content length after extraction: {len(content)} chars from {len(content_parts)} parts")

            if len(content) < 200:
                logger.warning(f"Content too short for {url}: {len(content)} chars")
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
            'oferta especial',
            'lea también',
            'le puede interesar',
            'más noticias',
            'contenido relacionado'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in promo_indicators)

    def _is_navigation_text(self, text: str) -> bool:
        """Check if text is navigation or UI element text"""
        nav_indicators = [
            'compartir',
            'facebook',
            'twitter',
            'whatsapp',
            'comentarios',
            'guardar',
            'imprimir',
            'reportar error',
            'siguiente',
            'anterior',
            'volver',
            'inicio',
            'menú'
        ]
        text_lower = text.lower()
        # Navigation text is usually short
        if len(text) < 50:
            return any(indicator in text_lower for indicator in nav_indicators)
        return False

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
        """Extract article author with multiple fallback strategies"""
        # Try structured data first (most reliable)
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                import json
                data = json.loads(json_ld.string)
                if isinstance(data, dict) and 'author' in data:
                    author_data = data['author']
                    if isinstance(author_data, dict) and 'name' in author_data:
                        return self._clean_text(author_data['name'])
                    elif isinstance(author_data, str):
                        return self._clean_text(author_data)
            except:
                pass

        # Try CSS selectors
        author_selectors = [
            'span[itemprop="author"]',
            'a[itemprop="author"]',
            '.author-name',
            '.byline',
            '.firma',
            '.autor-nombre',
            '.autor',
            '.redaccion-portafolio'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                # Clean prefixes
                author_text = re.sub(r'^(Por:?\s*|Redacción\s*|@)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2 and len(author_text) < 100:
                    return author_text

        # Try meta tags
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta and author_meta.get('content'):
            return self._clean_text(author_meta.get('content'))

        return "Portafolio"

    def _extract_date(self, soup: BeautifulSoup, url: str) -> Optional[datetime]:
        """Extract publication date with multiple fallback strategies"""
        # Try structured data first (most reliable)
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                import json
                data = json.loads(json_ld.string)
                if isinstance(data, dict):
                    for date_field in ['datePublished', 'dateCreated', 'publishedDate']:
                        if date_field in data:
                            try:
                                return datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
                            except:
                                pass
            except:
                pass

        # Try time element with itemprop
        time_elem = soup.select_one('time[itemprop="datePublished"]')
        if not time_elem:
            time_elem = soup.select_one('time[datetime]')
        if not time_elem:
            time_elem = soup.select_one('time')

        if time_elem:
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                try:
                    return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                except:
                    pass
            # Try text content
            date_text = self._clean_text(time_elem.get_text())
            if date_text:
                parsed_date = self._parse_spanish_date(date_text)
                if parsed_date:
                    return parsed_date

        # Try meta tags
        meta_date = soup.find('meta', property='article:published_time')
        if not meta_date:
            meta_date = soup.find('meta', attrs={'name': 'publish-date'})
        if meta_date and meta_date.get('content'):
            try:
                return datetime.fromisoformat(meta_date.get('content').replace('Z', '+00:00'))
            except:
                pass

        # Try date selectors
        date_selectors = ['.fecha', '.article-date', '.publish-date', '.date']
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
        """Parse Spanish date formats with comprehensive pattern matching"""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        # Clean date text
        date_text = date_text.lower().strip()

        # Date patterns (order matters - try most specific first)
        patterns = [
            # "28 oct 2025 - 8:55 p. m." or "28 oct 2025"
            (r'(\d{1,2})\s+(\w+)\s+(\d{4})', 'day_month_year'),
            # "15 de enero de 2024"
            (r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', 'day_de_month_de_year'),
            # "enero 15, 2024"
            (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', 'month_day_year'),
            # "15/01/2024"
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', 'day_month_year_slash'),
            # "2024-01-15"
            (r'(\d{4})-(\d{2})-(\d{2})', 'year_month_day_dash'),
        ]

        for pattern, pattern_type in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    groups = match.groups()

                    if pattern_type == 'day_month_year':
                        day, month_name, year = groups
                        month = months.get(month_name[:3])  # Use first 3 chars for abbreviations
                        if month:
                            return datetime(int(year), month, int(day))

                    elif pattern_type == 'day_de_month_de_year':
                        day, month_name, year = groups
                        month = months.get(month_name)
                        if month:
                            return datetime(int(year), month, int(day))

                    elif pattern_type == 'month_day_year':
                        month_name, day, year = groups
                        month = months.get(month_name)
                        if month:
                            return datetime(int(year), month, int(day))

                    elif pattern_type == 'day_month_year_slash':
                        day, month, year = groups
                        return datetime(int(year), int(month), int(day))

                    elif pattern_type == 'year_month_day_dash':
                        year, month, day = groups
                        return datetime(int(year), int(month), int(day))

                except (ValueError, TypeError):
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