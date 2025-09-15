"""
El Tiempo newspaper scraper implementation
Colombia's largest national newspaper
"""

import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from scrapers.base.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ElTiempoScraper(BaseScraper):
    """Scraper for El Tiempo (eltiempo.com)"""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.sections = [
            'politica',
            'economia',
            'justicia',
            'bogota',
            'colombia',
            'internacional',
            'deportes',
            'cultura'
        ]

        # CSS selectors specific to El Tiempo's structure
        self.selectors = {
            'article_links': 'article a, h2 a, h3 a',
            'title': 'h1.titulo, h1[class*="title"], h1',
            'subtitle': 'h2.sumario, .lead, .article-lead',
            'content': '.articulo-contenido, .article-body, .content-body',
            'author': '.autor-nombre, .author-name, .by-author',
            'date': '.fecha, time, .published-date',
            'category': '.categoria, .section-name',
            'tags': '.tags a, .article-tags a'
        }

        # Colombian entities patterns
        self.colombian_patterns = {
            'institutions': [
                r'\b(MinDefensa|Mindefensa|Ministerio de Defensa)\b',
                r'\b(Fiscalía|Fiscalia)\b',
                r'\b(Procuraduría|Procuraduria)\b',
                r'\b(Contraloría|Contraloria)\b',
                r'\b(Congreso|Senado|Cámara de Representantes)\b',
                r'\b(Corte Suprema|Corte Constitucional)\b',
                r'\b(Presidencia|Casa de Nariño)\b',
                r'\b(DANE|Banco de la República)\b',
                r'\b(FARC|ELN|EPL)\b',
                r'\b(Policía Nacional|Ejército Nacional|Armada Nacional|Fuerza Aérea)\b'
            ],
            'locations': [
                r'\b(Bogotá|Medellín|Cali|Barranquilla|Cartagena|Cúcuta|Bucaramanga)\b',
                r'\b(Antioquia|Valle del Cauca|Cundinamarca|Atlántico|Santander)\b',
                r'\b(Amazonas|Chocó|Nariño|Cauca|Meta|Arauca|Putumayo)\b'
            ],
            'political_figures': [
                r'\b(Petro|Gustavo Petro)\b',
                r'\b(Francia Márquez|Francia Marquez)\b',
                r'\b(Iván Duque|Ivan Duque)\b',
                r'\b(Álvaro Uribe|Alvaro Uribe)\b',
                r'\b(Juan Manuel Santos)\b'
            ],
            'economic_terms': [
                r'\b(peso colombiano|COP|pesos)\b',
                r'\b(UVR|UVT|salario mínimo)\b',
                r'\b(Ecopetrol|Avianca|Grupo Éxito)\b',
                r'\b(café|petróleo|carbón|oro|esmeraldas)\b'
            ]
        }

    async def get_article_urls(self) -> List[str]:
        """Get list of article URLs from El Tiempo sections"""
        all_urls = set()

        for section in self.sections:
            section_url = f"{self.base_url}/{section}"
            logger.info(f"Fetching section: {section_url}")

            html = await self.fetch_page(section_url)
            if html:
                soup = self.parse_html(html)
                links = soup.select(self.selectors['article_links'])

                for link in links:
                    href = link.get('href', '')
                    if href:
                        # Handle relative URLs
                        if href.startswith('/'):
                            href = self.base_url + href
                        # Filter for article URLs
                        if self._is_article_url(href):
                            all_urls.add(href)

        return list(all_urls)

    def _is_article_url(self, url: str) -> bool:
        """Check if URL is likely an article"""
        # El Tiempo article patterns
        article_patterns = [
            r'/\d{4}/\d{2}/\d{2}/',  # Date pattern
            r'/article/',
            r'/noticia/',
            r'-\d{6,}',  # Article ID pattern
        ]

        # Exclude patterns
        exclude_patterns = [
            r'/tema/',
            r'/seccion/',
            r'/autor/',
            r'/multimedia/',
            r'/podcast/',
            r'/opinion/',
            r'#',
            r'mailto:',
        ]

        # Check if URL matches article pattern
        has_article_pattern = any(re.search(pattern, url) for pattern in article_patterns)

        # Check if URL should be excluded
        should_exclude = any(re.search(pattern, url) for pattern in exclude_patterns)

        return has_article_pattern and not should_exclude

    def parse_article(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse El Tiempo article content"""
        try:
            article = {}

            # Extract title
            title_elem = soup.select_one(self.selectors['title'])
            if not title_elem:
                logger.warning(f"No title found for {url}")
                return None
            article['title'] = self.clean_text(title_elem.get_text())

            # Extract subtitle
            subtitle_elem = soup.select_one(self.selectors['subtitle'])
            article['subtitle'] = self.clean_text(subtitle_elem.get_text()) if subtitle_elem else ""

            # Extract content
            content_elem = soup.select_one(self.selectors['content'])
            if not content_elem:
                logger.warning(f"No content found for {url}")
                return None

            # Get all paragraphs from content
            paragraphs = content_elem.find_all('p')
            content_text = ' '.join([self.clean_text(p.get_text()) for p in paragraphs])

            # Check for paywall
            if self._is_paywall_content(content_text):
                article['is_paywall'] = True
                logger.info(f"Paywall detected for {url}")

            article['content'] = content_text

            # Extract author
            author_elem = soup.select_one(self.selectors['author'])
            article['author'] = self.clean_text(author_elem.get_text()) if author_elem else "El Tiempo"

            # Extract date
            date_elem = soup.select_one(self.selectors['date'])
            if date_elem:
                article['published_date'] = self._parse_date(date_elem)
            else:
                article['published_date'] = datetime.utcnow().isoformat()

            # Extract category from URL or page
            article['category'] = self._extract_category(url, soup)

            # Extract tags
            tags = soup.select(self.selectors['tags'])
            article['tags'] = [self.clean_text(tag.get_text()) for tag in tags]

            # Extract Colombian entities
            article['colombian_entities'] = self._extract_colombian_entities(content_text)

            # Calculate difficulty score for language learning
            article['difficulty_score'] = self._calculate_difficulty(content_text)

            # Word count for language learning
            article['word_count'] = len(content_text.split())

            return article

        except Exception as e:
            logger.error(f"Error parsing article {url}: {str(e)}")
            return None

    def _is_paywall_content(self, content: str) -> bool:
        """Check if content is behind paywall"""
        paywall_indicators = [
            'suscríbete',
            'contenido exclusivo',
            'acceso ilimitado',
            'hazte suscriptor',
            'lee esta historia'
        ]

        content_lower = content.lower()
        # Short content might indicate paywall
        if len(content) < 200:
            return True

        # Check for paywall keywords
        return any(indicator in content_lower for indicator in paywall_indicators)

    def _parse_date(self, date_elem) -> str:
        """Parse date from various formats"""
        date_text = self.clean_text(date_elem.get_text())

        # Try to parse ISO format from datetime attribute
        if date_elem.get('datetime'):
            return date_elem.get('datetime')

        # Colombian date formats
        date_patterns = [
            r'(\d{1,2}) de (\w+) de (\d{4})',  # "15 de enero de 2024"
            r'(\d{1,2})/(\d{1,2})/(\d{4})',     # "15/01/2024"
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                # Convert to ISO format
                # This is simplified - would need proper month name conversion
                return datetime.utcnow().isoformat()

        return datetime.utcnow().isoformat()

    def _extract_category(self, url: str, soup: BeautifulSoup) -> str:
        """Extract article category"""
        # Try to get from page
        category_elem = soup.select_one(self.selectors['category'])
        if category_elem:
            return self.clean_text(category_elem.get_text())

        # Extract from URL
        for section in self.sections:
            if f'/{section}/' in url:
                return section

        return 'general'

    def _extract_colombian_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Colombian-specific entities from text"""
        entities = {}

        for entity_type, patterns in self.colombian_patterns.items():
            found_entities = set()
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                found_entities.update(matches)

            if found_entities:
                entities[entity_type] = list(found_entities)

        return entities

    def _calculate_difficulty(self, text: str) -> float:
        """
        Calculate text difficulty for language learners
        Based on sentence length, word frequency, and complexity
        """
        if not text:
            return 0.0

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Basic metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Difficulty factors
        difficulty = 0.0

        # Sentence length factor (longer = harder)
        if avg_sentence_length < 10:
            difficulty += 1.0  # Simple
        elif avg_sentence_length < 20:
            difficulty += 2.0  # Intermediate
        elif avg_sentence_length < 30:
            difficulty += 3.0  # Advanced
        else:
            difficulty += 4.0  # Expert

        # Word length factor
        if avg_word_length < 5:
            difficulty += 0.5
        elif avg_word_length < 7:
            difficulty += 1.0
        else:
            difficulty += 1.5

        # Complex vocabulary indicators
        complex_indicators = [
            r'\b\w{12,}\b',  # Very long words
            r'\b[A-Z]{3,}\b',  # Acronyms
            r'\d+[,.]?\d*%?',  # Numbers and percentages
        ]

        for indicator in complex_indicators:
            matches = re.findall(indicator, text)
            difficulty += len(matches) * 0.1

        # Normalize to 1-5 scale
        difficulty = min(5.0, max(1.0, difficulty))

        return round(difficulty, 1)