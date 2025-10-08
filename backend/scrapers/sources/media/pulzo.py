"""
Pulzo digital news scraper implementation
Colombia's leading digital native news site
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging

from scrapers.base.smart_scraper import SmartScraper, ScrapedDocument

logger = logging.getLogger(__name__)


class PulzoScraper(SmartScraper):
    """Scraper for Pulzo (pulzo.com)"""

    def __init__(self, source_config: Dict = None):
        config = source_config or {
            'name': 'Pulzo',
            'url': 'https://www.pulzo.com',
            'rate_limit': '12/minute'
        }
        super().__init__(config)

        self.sections = [
            'nacion',
            'bogota',
            'mundo',
            'economia',
            'deportes',
            'entretenimiento',
            'tecnologia',
            'opinion',
            'viral'
        ]

        # CSS selectors for Pulzo's structure
        self.selectors = {
            'article_links': '.article-link, .story-link, .card-link, .news-link, h2 a, h3 a',
            'title': 'h1.article-title, h1.story-title, h1.news-title, h1',
            'subtitle': '.article-subtitle, .story-subtitle, .bajada, .entradilla',
            'content': '.article-content, .story-content, .content-body, .news-content',
            'author': '.article-author, .story-author, .byline, .autor',
            'date': '.article-date, .story-date, time, .publish-date',
            'category': '.article-category, .story-category, .seccion',
            'tags': '.article-tags a, .story-tags a, .tags a'
        }

    def extract_article_urls(self, homepage_html: str) -> List[str]:
        """Extract article URLs from Pulzo homepage"""
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

        # Get articles from digital news sections
        for section in self.sections[:6]:  # Focus on news sections
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
        """Check if URL is a valid Pulzo article"""
        # Digital news article indicators
        article_indicators = [
            '/nacion/',
            '/bogota/',
            '/mundo/',
            '/economia/',
            '/deportes/',
            '/entretenimiento/',
            '/tecnologia/',
            '/viral/',
            '/articulo/',
            '/noticia/'
        ]

        # Exclude patterns
        exclude_patterns = [
            '/autor/',
            '/tag/',
            '/categoria/',
            '/multimedia/',
            '/video/',
            '/galeria/',
            '/live/',
            '/transmision/',
            '/especial/',
            '/directorio/',
            '#',
            'mailto:',
            'javascript:',
            '.pdf',
            '.jpg',
            '.png',
            'twitter.com',
            'facebook.com',
            'instagram.com',
            'youtube.com'
        ]

        # Check indicators
        has_indicator = any(indicator in url.lower() for indicator in article_indicators)

        # Check exclusions
        should_exclude = any(pattern in url.lower() for pattern in exclude_patterns)

        # Check for article ID pattern
        has_id = bool(re.search(r'/\d{5,}', url))

        return (has_indicator or has_id) and not should_exclude

    def extract_article_content(self, article_html: str, url: str) -> Optional[ScrapedDocument]:
        """Extract content from Pulzo article"""
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
                    # Skip promotional content
                    if not self._is_promotional_content(text):
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

            # Digital native news specific analysis
            digital_features = self._analyze_digital_features(content, soup)
            content_type = self._classify_digital_content(content, url)
            social_relevance = self._analyze_social_relevance(content)
            difficulty = self._calculate_digital_difficulty(content)

            # Create document
            doc = ScrapedDocument(
                source=self.source_name,
                source_type='digital_news',
                url=url,
                title=title,
                content=content,
                author=author,
                published_date=published_date,
                metadata={
                    'category': category,
                    'digital_features': digital_features,
                    'content_type': content_type,
                    'social_relevance': social_relevance,
                    'word_count': len(content.split()),
                    'source_type': 'digital_native',
                    'target_audience': 'digital_natives',
                    'content_style': 'accessible'
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

    def _is_promotional_content(self, text: str) -> bool:
        """Check if text is promotional content"""
        promo_indicators = [
            'suscríbete',
            'descarga la app',
            'síguenos',
            'pulzo',
            'red de noticias',
            'boletín',
            'newsletter',
            'notificaciones',
            'compartir',
            'redes sociales'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in promo_indicators) and len(text) < 100

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

        return "Pulzo"

    def _extract_date(self, soup: BeautifulSoup, url: str) -> Optional[datetime]:
        """Extract publication date with support for relative times"""
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
                parsed_date = self._parse_digital_date(date_text)
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
                if category and category.lower() not in ['inicio', 'home', 'pulzo']:
                    return category

        # Extract from URL
        category_map = {
            'nacion': 'Nacional',
            'bogota': 'Bogotá',
            'mundo': 'Internacional',
            'economia': 'Economía',
            'deportes': 'Deportes',
            'entretenimiento': 'Entretenimiento',
            'tecnologia': 'Tecnología',
            'opinion': 'Opinión',
            'viral': 'Viral'
        }

        for section, category in category_map.items():
            if section in url.lower():
                return category

        return 'Noticias'

    def _analyze_digital_features(self, content: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze digital-native features of the content"""
        features = {}

        # Social media integration
        social_elements = soup.find_all(['iframe', 'blockquote', 'embed'])
        features['social_embeds'] = len([elem for elem in social_elements
                                       if any(platform in str(elem).lower()
                                            for platform in ['twitter', 'facebook', 'instagram', 'youtube'])])

        # Interactive elements
        interactive_elements = soup.find_all(['video', 'audio', 'canvas', 'svg'])
        features['interactive_elements'] = len(interactive_elements)

        # Real-time content indicators
        content_lower = content.lower()
        realtime_indicators = ['en vivo', 'minuto a minuto', 'última hora', 'breaking', 'ahora']
        features['realtime_content'] = any(indicator in content_lower for indicator in realtime_indicators)

        # Viral content indicators
        viral_indicators = ['viral', 'trending', 'se vuelve viral', 'redes sociales', 'video viral']
        features['viral_content'] = any(indicator in content_lower for indicator in viral_indicators)

        # Mobile-first indicators
        mobile_indicators = ['app', 'móvil', 'celular', 'smartphone', 'whatsapp']
        features['mobile_mentions'] = sum(1 for indicator in mobile_indicators if indicator in content_lower)

        return features

    def _classify_digital_content(self, content: str, url: str) -> str:
        """Classify the type of digital content"""
        content_lower = content.lower()

        # Breaking news
        breaking_indicators = ['última hora', 'breaking', 'urgente', 'en desarrollo']
        if any(indicator in content_lower for indicator in breaking_indicators):
            return 'breaking_news'

        # Viral content
        viral_indicators = ['viral', 'redes sociales', 'trending', 'se vuelve viral']
        if any(indicator in content_lower for indicator in viral_indicators) or '/viral/' in url:
            return 'viral_content'

        # Entertainment
        entertainment_indicators = ['celebridad', 'famoso', 'artista', 'cantante', 'actor', 'reality']
        if any(indicator in content_lower for indicator in entertainment_indicators) or '/entretenimiento/' in url:
            return 'entertainment'

        # Technology
        tech_indicators = ['app', 'aplicación', 'tecnología', 'digital', 'internet', 'redes']
        if any(indicator in content_lower for indicator in tech_indicators) or '/tecnologia/' in url:
            return 'technology'

        # Sports
        if '/deportes/' in url or any(word in content_lower for word in ['fútbol', 'deporte', 'equipo', 'jugador']):
            return 'sports'

        # Economy
        if '/economia/' in url or any(word in content_lower for word in ['economía', 'empresa', 'mercado', 'precio']):
            return 'economy'

        # Local news
        local_indicators = ['bogotá', 'medellín', 'cali', 'alcalde', 'local', 'ciudad']
        if any(indicator in content_lower for indicator in local_indicators) or '/bogota/' in url:
            return 'local_news'

        return 'general_news'

    def _analyze_social_relevance(self, content: str) -> Dict[str, Any]:
        """Analyze social media and digital relevance"""
        relevance = {}

        content_lower = content.lower()

        # Social platform mentions
        platforms = ['twitter', 'facebook', 'instagram', 'tiktok', 'youtube', 'whatsapp']
        platform_mentions = {platform: platform in content_lower for platform in platforms}
        relevance['platform_mentions'] = platform_mentions

        # Social engagement indicators
        engagement_indicators = ['comentarios', 'likes', 'compartir', 'viral', 'trending', 'hashtag']
        engagement_count = sum(1 for indicator in engagement_indicators if indicator in content_lower)
        relevance['engagement_indicators'] = engagement_count

        # Digital culture terms
        digital_culture = ['meme', 'gif', 'emoji', 'influencer', 'youtuber', 'tiktoker', 'streamer']
        digital_count = sum(1 for term in digital_culture if term in content_lower)
        relevance['digital_culture_terms'] = digital_count

        # Generation indicators
        generation_terms = ['millennial', 'gen z', 'centennial', 'jóvenes', 'adolescentes']
        generation_count = sum(1 for term in generation_terms if term in content_lower)
        relevance['generation_focus'] = generation_count

        # Calculate overall social relevance score
        total_social = engagement_count + digital_count + generation_count
        relevance['social_relevance_score'] = min(10.0, total_social / max(1, len(content.split())) * 1000)

        return relevance

    def _calculate_digital_difficulty(self, text: str) -> float:
        """Calculate difficulty for digital native content"""
        if not text:
            return 2.0  # Digital content is typically accessible

        words = text.split()
        sentences = re.split(r'[.!?]+', text)

        # Metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Digital-specific factors
        colloquial_language = len(re.findall(r'\b(súper|mega|genial|brutal|chimba|berraco)\b', text, re.IGNORECASE))
        english_terms = len(re.findall(r'\b(app|like|follow|post|story|live|streaming)\b', text, re.IGNORECASE))
        youth_slang = len(re.findall(r'\b(lit|cringe|random|crush|hater|fake)\b', text, re.IGNORECASE))
        abbreviations = len(re.findall(r'\b[A-Z]{2,5}\b', text))

        # Start low for digital content (accessible)
        difficulty = 1.8

        # Sentence complexity
        if avg_sentence_length > 15:
            difficulty += 0.2
        if avg_sentence_length > 22:
            difficulty += 0.3

        # Word complexity
        if avg_word_length > 6:
            difficulty += 0.2

        # Digital factors
        difficulty -= min(0.3, colloquial_language / 30)  # Colloquial language is easier
        difficulty += min(0.2, english_terms / 40)  # English terms add slight complexity
        difficulty -= min(0.2, youth_slang / 20)  # Youth slang can be accessible
        difficulty += min(0.3, abbreviations / 25)  # Abbreviations can be confusing

        return min(5.0, max(1.0, difficulty))

    def _get_difficulty_level(self, score: float) -> str:
        """Convert difficulty score to level for digital content"""
        if score < 1.8:
            return 'Principiante'
        elif score < 2.3:
            return 'Intermedio'
        elif score < 2.9:
            return 'Intermedio-Avanzado'
        elif score < 3.5:
            return 'Avanzado'
        else:
            return 'Experto'

    def _parse_digital_date(self, date_text: str) -> Optional[datetime]:
        """Parse digital-style date formats including relative times"""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        # Digital date patterns
        patterns = [
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',  # "15 de enero de 2024"
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',          # "enero 15, 2024"
            r'(\d{1,2})/(\d{1,2})/(\d{4})',            # "15/01/2024"
            r'(\d{4})-(\d{2})-(\d{2})',                # "2024-01-15"
            r'Hace\s+(\d+)\s+(hora|día|minuto)s?',     # "Hace 2 horas"
            r'(\d+)\s+(hora|día|minuto)s?\s+atrás',    # "2 horas atrás"
            r'Hoy\s+(\d{1,2}):(\d{2})',                # "Hoy 14:30"
            r'Ayer\s+(\d{1,2}):(\d{2})',               # "Ayer 14:30"
            r'Ahora',                                   # "Ahora"
            r'Recién',                                  # "Recién"
            r'En vivo'                                  # "En vivo"
        ]

        for pattern in patterns:
            match = re.search(pattern, date_text, re.IGNORECASE)
            if match:
                try:
                    if 'Hace' in pattern or 'atrás' in pattern:
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
                    elif 'Hoy' in pattern:
                        hour, minute = match.groups()
                        today = datetime.utcnow().date()
                        return datetime.combine(today, datetime.min.time().replace(hour=int(hour), minute=int(minute)))
                    elif 'Ayer' in pattern:
                        hour, minute = match.groups()
                        yesterday = datetime.utcnow().date() - timedelta(days=1)
                        return datetime.combine(yesterday, datetime.min.time().replace(hour=int(hour), minute=int(minute)))
                    elif any(word in pattern for word in ['Ahora', 'Recién', 'En vivo']):
                        return datetime.utcnow()
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