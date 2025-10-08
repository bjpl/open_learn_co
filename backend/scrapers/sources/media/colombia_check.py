"""
Colombia Check scraper implementation
Colombia's leading fact-checking organization
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class ColombiaCheckScraper(SmartScraper):
    """Scraper for Colombia Check (colombiacheck.com)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'Colombia Check',
            'url': 'https://colombiacheck.com',
            'rate_limit': '8/minute'
        }
        super().__init__(config)

        self.sections = [
            'fact-check',
            'chequeos',
            'politica',
            'salud',
            'economia',
            'elecciones',
            'desinformacion',
            'explicadores'
        ]

        # CSS selectors for Colombia Check's structure
        self.selectors = {
            'article_links': '.fact-check-link, .article-link, .story-link, .card-link, h2 a, h3 a',
            'title': 'h1.fact-check-title, h1.article-title, h1.story-title, h1',
            'subtitle': '.fact-check-subtitle, .article-subtitle, .bajada, .dek',
            'content': '.fact-check-content, .article-content, .story-content, .content-body',
            'author': '.fact-check-author, .article-author, .byline, .autor',
            'date': '.fact-check-date, .article-date, time, .publish-date',
            'category': '.fact-check-category, .article-category, .section',
            'tags': '.fact-check-tags a, .article-tags a, .tags a',
            'verdict': '.verdict, .calificacion, .resultado'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from Colombia Check homepage"""
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

        # Get articles from fact-checking sections
        for section in self.sections[:6]:  # Focus on fact-checking sections
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
        """Check if URL is a valid Colombia Check article"""
        # Fact-checking article indicators
        article_indicators = [
            '/fact-check/',
            '/chequeos/',
            '/politica/',
            '/salud/',
            '/economia/',
            '/elecciones/',
            '/desinformacion/',
            '/explicadores/',
            '/articulo/',
            '/chequeo/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/autor/',
            '/tag/',
            '/categoria/',
            '/multimedia/',
            '/video/',
            '/galeria/',
            '/evento/',
            '/team/',
            '/about/',
            '/metodologia/',
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
        """Extract content from Colombia Check article"""
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

            # Fact-checking specific features
            verdict = self._extract_verdict(soup)
            fact_check_analysis = self._analyze_fact_check_content(content, verdict)
            sources = self._extract_sources(content)
            difficulty = self._calculate_fact_check_difficulty(content)

            # Create document
            doc = ScrapedDocument(
                source=self.source_name,
                source_type='fact_check',
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                metadata={
                    'category': category,
                    'verdict': verdict,
                    'fact_check_analysis': fact_check_analysis,
                    'sources': sources,
                    'word_count': len(content.split()),
                    'source_focus': 'fact_checking',
                    'target_audience': 'general_public',
                    'verification_type': 'journalistic'
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Colombia',
                categories=[category] if category else ['verificación']
            )

            return doc

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    def _is_promotional_content(self, text: str) -> bool:
        """Check if text is promotional content"""
        promo_indicators = [
            'colombia check',
            'suscríbete',
            'síguenos',
            'donaciones',
            'apoya',
            'newsletter',
            'metodología',
            'consorcio'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in promo_indicators) and len(text) < 80

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        author_selectors = [
            '.fact-check-author',
            '.article-author',
            '.byline',
            '.autor',
            '.verificador'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                # Clean prefixes
                author_text = re.sub(r'^(Por:?\s*|Verificado por:?\s*|@)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return author_text

        return "Colombia Check"

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
        date_selectors = ['.fact-check-date', '.article-date', '.publish-date', '.fecha']
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
        category_selectors = ['.fact-check-category', '.article-category', '.section']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category and category.lower() not in ['inicio', 'home', 'colombia check']:
                    return category

        # Extract from URL
        category_map = {
            'fact-check': 'Verificación',
            'chequeos': 'Chequeos',
            'politica': 'Política',
            'salud': 'Salud',
            'economia': 'Economía',
            'elecciones': 'Elecciones',
            'desinformacion': 'Desinformación',
            'explicadores': 'Explicadores'
        }

        for section, category in category_map.items():
            if section in url.lower():
                return category

        return 'Verificación'

    def _extract_verdict(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract fact-check verdict"""
        verdict_selectors = ['.verdict', '.calificacion', '.resultado', '.rating']

        for selector in verdict_selectors:
            verdict_elem = soup.select_one(selector)
            if verdict_elem:
                verdict_text = self._clean_text(verdict_elem.get_text())
                if verdict_text:
                    return self._normalize_verdict(verdict_text)

        return None

    def _normalize_verdict(self, verdict_text: str) -> str:
        """Normalize verdict to standard categories"""
        verdict_lower = verdict_text.lower()

        # True/accurate
        if any(word in verdict_lower for word in ['verdadero', 'cierto', 'correcto', 'verdad']):
            return 'Verdadero'

        # False/inaccurate
        if any(word in verdict_lower for word in ['falso', 'incorrecto', 'mentira', 'fake']):
            return 'Falso'

        # Partially true
        if any(word in verdict_lower for word in ['parcialmente', 'medias', 'incompleto']):
            return 'Parcialmente Cierto'

        # Misleading
        if any(word in verdict_lower for word in ['engañoso', 'misleading', 'confuso']):
            return 'Engañoso'

        # Unverifiable
        if any(word in verdict_lower for word in ['inverificable', 'sin evidencia', 'insuficiente']):
            return 'Inverificable'

        # Exaggerated
        if any(word in verdict_lower for word in ['exagerado', 'inflado', 'desproporcionado']):
            return 'Exagerado'

        return verdict_text

    def _analyze_fact_check_content(self, content: str, verdict: Optional[str]) -> Dict[str, Any]:
        """Analyze fact-checking methodology and content"""
        analysis = {}

        content_lower = content.lower()

        # Evidence indicators
        evidence_indicators = [
            'según', 'datos', 'estadística', 'cifras', 'documento',
            'fuente', 'evidencia', 'prueba', 'registro'
        ]

        # Verification indicators
        verification_indicators = [
            'verificamos', 'consultamos', 'revisamos', 'confirmamos',
            'contactamos', 'investigamos', 'indagamos'
        ]

        # Source indicators
        source_indicators = [
            'oficial', 'autoridad', 'institución', 'experto',
            'especialista', 'organización', 'entidad'
        ]

        # Methodology indicators
        methodology_indicators = [
            'metodología', 'proceso', 'criterio', 'análisis',
            'comparación', 'verificación', 'chequeo'
        ]

        evidence_count = sum(1 for indicator in evidence_indicators if indicator in content_lower)
        verification_count = sum(1 for indicator in verification_indicators if indicator in content_lower)
        source_count = sum(1 for indicator in source_indicators if indicator in content_lower)
        methodology_count = sum(1 for indicator in methodology_indicators if indicator in content_lower)

        total_fact_check = max(1, evidence_count + verification_count + source_count + methodology_count)

        analysis['evidence_ratio'] = evidence_count / total_fact_check
        analysis['verification_ratio'] = verification_count / total_fact_check
        analysis['source_ratio'] = source_count / total_fact_check
        analysis['methodology_ratio'] = methodology_count / total_fact_check

        # Quality score
        quality_score = (evidence_count * 0.3 + verification_count * 0.3 +
                        source_count * 0.2 + methodology_count * 0.2) / len(content.split()) * 1000

        analysis['quality_score'] = min(10.0, quality_score)
        analysis['verdict'] = verdict

        return analysis

    def _extract_sources(self, content: str) -> List[str]:
        """Extract sources mentioned in the fact-check"""
        sources = []

        # Common source patterns
        source_patterns = [
            r'según ([A-Z][^,.]{10,50})',
            r'de acuerdo con ([A-Z][^,.]{10,50})',
            r'fuente: ([A-Z][^,.]{10,50})',
            r'consultamos a ([A-Z][^,.]{10,50})',
            r'([A-Z][^,.]{10,50}) confirmó',
            r'([A-Z][^,.]{10,50}) indicó',
            r'([A-Z][^,.]{10,50}) señaló'
        ]

        for pattern in source_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            sources.extend(matches)

        # Clean and deduplicate sources
        cleaned_sources = []
        for source in sources[:10]:  # Limit to 10 sources
            source = self._clean_text(source)
            if len(source) > 5 and source not in cleaned_sources:
                cleaned_sources.append(source)

        return cleaned_sources

    def _calculate_fact_check_difficulty(self, text: str) -> float:
        """Calculate difficulty for fact-checking content"""
        if not text:
            return 2.8  # Fact-checks should be accessible

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Fact-checking specific factors
        technical_terms = len(re.findall(r'\b(metodología|verificación|desinformación|fact-checking)\b', text, re.IGNORECASE))
        numbers_data = len(re.findall(r'\d+[.,]?\d*\s*%|\d+[.,]?\d*\s*(millones?|mil)', text))
        explanatory_language = len(re.findall(r'\b(es decir|esto significa|en otras palabras|por ejemplo)\b', text, re.IGNORECASE))

        # Start moderate for fact-checking content
        difficulty = 2.6

        # Sentence complexity
        if avg_sentence_length > 18:
            difficulty += 0.3
        if avg_sentence_length > 25:
            difficulty += 0.3

        # Word complexity
        if avg_word_length > 6.5:
            difficulty += 0.2

        # Content factors
        difficulty += min(0.4, technical_terms / 20)
        difficulty += min(0.3, numbers_data / 30)
        difficulty -= min(0.3, explanatory_language / 20)  # Explanatory language makes it easier

        return min(5.0, max(1.0, difficulty))

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for fact-checking content"""
        if score < 2.5:
            return 'Principiante'
        elif score < 3.0:
            return 'Intermedio'
        elif score < 3.7:
            return 'Intermedio-Avanzado'
        elif score < 4.3:
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