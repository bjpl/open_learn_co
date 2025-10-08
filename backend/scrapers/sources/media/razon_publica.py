"""
Razón Pública scraper implementation
Colombia's leading academic and policy analysis platform
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class RazonPublicaScraper(SmartScraper):
    """Scraper for Razón Pública (razonpublica.com)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'Razón Pública',
            'url': 'https://www.razonpublica.com',
            'rate_limit': '5/minute'
        }
        super().__init__(config)

        self.sections = [
            'politica-gobierno',
            'economia-sociedad',
            'conflicto-drogas-paz',
            'internacional',
            'educacion',
            'cultura',
            'index.php/politica-gobierno',
            'index.php/economia-sociedad'
        ]

        # CSS selectors for Razón Pública's structure
        self.selectors = {
            'article_links': '.article-link, .content-link, .item-link, .headline-link, h2 a, h3 a',
            'title': 'h1.article-title, h1.content-title, h1.item-title, h1',
            'subtitle': '.article-subtitle, .content-subtitle, .bajada, .dek',
            'content': '.article-content, .content-body, .item-content, .article-text',
            'author': '.article-author, .content-author, .byline, .autor',
            'date': '.article-date, .content-date, time, .publish-date',
            'category': '.article-category, .content-category, .section',
            'tags': '.article-tags a, .content-tags a, .tags a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from Razón Pública homepage"""
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

        # Get articles from academic sections
        for section in self.sections[:5]:  # Focus on core academic sections
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
        """Check if URL is a valid Razón Pública article"""
        # Academic article indicators
        article_indicators = [
            '/politica-gobierno/',
            '/economia-sociedad/',
            '/conflicto-drogas-paz/',
            '/internacional/',
            '/educacion/',
            '/cultura/',
            '/index.php/',
            '/articulo/',
            '/analisis/'
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
            '/directorio/',
            '/component/',
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

        # Check for article ID pattern (Joomla style)
        has_id = bool(re.search(r'/\d{3,}', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from Razón Pública article"""
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
                if text and len(text) > 40:
                    # Skip promotional content
                    if not self._is_promotional_content(text):
                        content_parts.append(text)

            content = ' '.join(content_parts)

            # Validate content
            if len(content) < 400:
                logger.warning(f"Content too short for {url}")
                return None

            # Extract metadata
            author = self._extract_author(soup)
            published_date = self._extract_date(soup, url)
            category = self._extract_category(soup, url)

            # Academic analysis specific features
            entities = self._extract_academic_entities(content)
            academic_level = self._analyze_academic_level(content)
            policy_analysis = self._analyze_policy_content(content, url)
            difficulty = self._calculate_academic_difficulty(content)

            # Create document
            doc = ScrapedDocument(
                source=self.source_name,
                source_type='academic_analysis',
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                metadata={
                    'category': category,
                    'academic_entities': entities,
                    'academic_level': academic_level,
                    'policy_analysis': policy_analysis,
                    'word_count': len(content.split()),
                    'source_focus': 'policy_research',
                    'target_audience': 'academics_policymakers',
                    'content_depth': 'scholarly_analysis'
                },
                language='es',
                difficulty_level=self._get_difficulty_level(difficulty),
                region='Colombia',
                categories=[category] if category else ['análisis']
            )

            return doc

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    def _is_promotional_content(self, text: str) -> bool:
        """Check if text is promotional content"""
        promo_indicators = [
            'razón pública',
            'fundación',
            'apoya',
            'donación',
            'suscríbete',
            'síguenos',
            'newsletter',
            'universidad nacional'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in promo_indicators) and len(text) < 100

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        author_selectors = [
            '.article-author',
            '.content-author',
            '.byline',
            '.autor',
            '.investigador'
        ]

        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = self._clean_text(author_elem.get_text())
                # Clean prefixes
                author_text = re.sub(r'^(Por:?\s*|@)', '', author_text, flags=re.IGNORECASE)
                if author_text and len(author_text) > 2:
                    return author_text

        return "Razón Pública"

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
        date_selectors = ['.article-date', '.content-date', '.publish-date', '.fecha']
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
        category_selectors = ['.article-category', '.content-category', '.section']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = self._clean_text(cat_elem.get_text())
                if category and category.lower() not in ['inicio', 'home', 'razón pública']:
                    return category

        # Extract from URL
        category_map = {
            'politica-gobierno': 'Política y Gobierno',
            'economia-sociedad': 'Economía y Sociedad',
            'conflicto-drogas-paz': 'Conflicto, Drogas y Paz',
            'internacional': 'Internacional',
            'educacion': 'Educación',
            'cultura': 'Cultura'
        }

        for section, category in category_map.items():
            if section in url.lower():
                return category

        return 'Análisis'

    def _extract_academic_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract academic institutions, researchers, and policy entities"""
        entities = {}

        patterns = {
            'universities': [
                r'\b(Universidad Nacional|Universidad de los Andes|Universidad Javeriana)\b',
                r'\b(Universidad del Rosario|Universidad Externado|Universidad Central)\b',
                r'\b(Universidad de Antioquia|Universidad del Valle|Universidad Industrial)\b'
            ],
            'research_centers': [
                r'\b(FEDESARROLLO|Centro de Estudios|Instituto de Estudios)\b',
                r'\b(CEDE|CIES|IEPRI|CID|CIJUS)\b',
                r'\b(Observatorio|Centro de Investigación)\b'
            ],
            'international_orgs': [
                r'\b(Banco Mundial|FMI|BID|CEPAL|PNUD)\b',
                r'\b(ONU|OEA|OCDE|UNESCO|UNICEF)\b',
                r'\b(Comisión Europea|Unión Europea)\b'
            ],
            'policy_institutions': [
                r'\b(DNP|CONPES|MinHacienda|MinEducación)\b',
                r'\b(DANE|ICFES|ICETEX|COLCIENCIAS)\b',
                r'\b(Consejo de Estado|Consejo Superior)\b'
            ],
            'think_tanks': [
                r'\b(Fundación Ideas para la Paz|FIP|Dejusticia)\b',
                r'\b(Centro de Pensamiento|Instituto de Ciencia Política)\b'
            ],
            'academic_concepts': [
                r'\b(política pública|gobernanza|institucionalidad)\b',
                r'\b(desarrollo económico|crecimiento económico|equidad)\b',
                r'\b(democracia|participación ciudadana|estado de derecho)\b'
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

    def _analyze_academic_level(self, content: str) -> Dict[str, Any]:
        """Analyze the academic rigor and complexity of content"""
        academic_analysis = {}

        content_lower = content.lower()

        # Academic indicators
        academic_indicators = [
            'según', 'de acuerdo con', 'investigación', 'estudio',
            'análisis', 'evidencia', 'datos', 'estadística'
        ]

        # Theoretical indicators
        theoretical_indicators = [
            'teoría', 'modelo', 'marco conceptual', 'paradigma',
            'enfoque', 'perspectiva teórica', 'literatura'
        ]

        # Citation indicators
        citation_indicators = [
            'autor', 'investigador', 'académico', 'experto',
            'especialista', 'scholar', 'paper', 'artículo'
        ]

        # Methodology indicators
        methodology_indicators = [
            'metodología', 'método', 'técnica', 'instrumento',
            'encuesta', 'entrevista', 'análisis cualitativo', 'cuantitativo'
        ]

        academic_count = sum(1 for indicator in academic_indicators if indicator in content_lower)
        theoretical_count = sum(1 for indicator in theoretical_indicators if indicator in content_lower)
        citation_count = sum(1 for indicator in citation_indicators if indicator in content_lower)
        methodology_count = sum(1 for indicator in methodology_indicators if indicator in content_lower)

        total_academic = max(1, academic_count + theoretical_count + citation_count + methodology_count)

        academic_analysis['empirical_ratio'] = academic_count / total_academic
        academic_analysis['theoretical_ratio'] = theoretical_count / total_academic
        academic_analysis['citation_ratio'] = citation_count / total_academic
        academic_analysis['methodology_ratio'] = methodology_count / total_academic

        # Academic rigor score
        rigor_score = (academic_count * 0.3 + theoretical_count * 0.3 +
                      citation_count * 0.2 + methodology_count * 0.2) / len(content.split()) * 1000

        academic_analysis['rigor_score'] = min(10.0, rigor_score)

        # Determine academic level
        if rigor_score > 8:
            academic_analysis['academic_level'] = 'high'
        elif rigor_score > 5:
            academic_analysis['academic_level'] = 'medium'
        else:
            academic_analysis['academic_level'] = 'accessible'

        return academic_analysis

    def _analyze_policy_content(self, content: str, url: str) -> Dict[str, Any]:
        """Analyze policy-related content and recommendations"""
        policy_analysis = {}

        content_lower = content.lower()

        # Policy indicators
        policy_indicators = [
            'política pública', 'política', 'programa', 'plan',
            'estrategia', 'iniciativa', 'reforma', 'regulación'
        ]

        # Recommendation indicators
        recommendation_indicators = [
            'recomienda', 'propone', 'sugiere', 'debería',
            'es necesario', 'se requiere', 'conviene'
        ]

        # Evaluation indicators
        evaluation_indicators = [
            'evalúa', 'analiza', 'examina', 'revisa',
            'impacto', 'efecto', 'resultado', 'consecuencia'
        ]

        policy_count = sum(1 for indicator in policy_indicators if indicator in content_lower)
        recommendation_count = sum(1 for indicator in recommendation_indicators if indicator in content_lower)
        evaluation_count = sum(1 for indicator in evaluation_indicators if indicator in content_lower)

        total_policy = max(1, policy_count + recommendation_count + evaluation_count)

        policy_analysis['policy_focus'] = policy_count / total_policy
        policy_analysis['recommendation_focus'] = recommendation_count / total_policy
        policy_analysis['evaluation_focus'] = evaluation_count / total_policy

        # Determine primary policy type
        if policy_analysis['recommendation_focus'] > 0.4:
            policy_analysis['policy_type'] = 'prescriptive'
        elif policy_analysis['evaluation_focus'] > 0.4:
            policy_analysis['policy_type'] = 'evaluative'
        elif policy_analysis['policy_focus'] > 0.3:
            policy_analysis['policy_type'] = 'descriptive'
        else:
            policy_analysis['policy_type'] = 'general_analysis'

        return policy_analysis

    def _calculate_academic_difficulty(self, text: str) -> float:
        """Calculate difficulty for academic content"""
        if not text:
            return 4.5  # Academic content is typically very complex

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Academic complexity factors
        academic_terms = len(re.findall(r'\b(epistemológico|metodológico|paradigmático|estructural)\b', text, re.IGNORECASE))
        latin_terms = len(re.findall(r'\b(per se|a priori|a posteriori|ad hoc|inter alia)\b', text, re.IGNORECASE))
        complex_concepts = len(re.findall(r'\b(institucionalidad|gobernanza|sostenibilidad|multidimensional)\b', text, re.IGNORECASE))
        citations = len(re.findall(r'\([12]\d{3}\)|et al\.|op\. cit\.', text))

        # Start very high for academic content
        difficulty = 4.3

        # Sentence complexity
        if avg_sentence_length > 28:
            difficulty += 0.3
        if avg_sentence_length > 38:
            difficulty += 0.4

        # Word complexity
        if avg_word_length > 8:
            difficulty += 0.4

        # Academic complexity
        difficulty += min(0.8, academic_terms / 10)
        difficulty += min(0.4, latin_terms / 5)
        difficulty += min(0.6, complex_concepts / 15)
        difficulty += min(0.3, citations / 10)

        return min(5.0, difficulty)

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for academic content"""
        if score < 4.0:
            return 'Avanzado'
        elif score < 4.5:
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