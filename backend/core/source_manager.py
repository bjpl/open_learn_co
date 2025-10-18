"""
Central source manager for orchestrating all data collection
"""

import yaml
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import importlib
import inspect

logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    """Represents a data source configuration"""
    category: str
    key: str
    name: str
    url: str
    type: str
    priority: str
    config: Dict[str, Any]

    @property
    def is_api(self) -> bool:
        return 'api_endpoint' in self.config

    @property
    def is_scraper(self) -> bool:
        return 'scraping_interval' in self.config or 'selectors' in self.config

    @property
    def update_interval(self) -> int:
        """Get update interval in minutes"""
        if 'scraping_interval' in self.config:
            return self.config['scraping_interval']
        elif 'update_frequency' in self.config:
            freq = self.config['update_frequency']
            if freq == 'daily':
                return 1440
            elif freq == 'hourly':
                return 60
            elif freq == 'weekly':
                return 10080
        return 60  # Default to hourly


class SourceManager:
    """
    Manages all data sources: APIs, scrapers, etc.
    """

    def __init__(self, config_path: str = None):
        """Initialize source manager"""
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'sources.yaml'
        self.sources: Dict[str, DataSource] = {}
        self.scheduler = AsyncIOScheduler()
        self.api_clients = {}
        self.scrapers = {}

        # Load configuration
        self.load_sources()

    def load_sources(self):
        """Load all source configurations from YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Parse all sources
            for category, sources in config.items():
                if isinstance(sources, dict):
                    for key, source_config in sources.items():
                        if isinstance(source_config, dict):
                            source = DataSource(
                                category=category,
                                key=key,
                                name=source_config.get('name', key),
                                url=source_config.get('url', ''),
                                type=source_config.get('type', 'unknown'),
                                priority=source_config.get('priority', 'low'),
                                config=source_config
                            )
                            self.sources[f"{category}.{key}"] = source
                        else:
                            # Handle nested categories (like media.national)
                            for sub_key, sub_config in source_config.items():
                                if isinstance(sub_config, dict):
                                    source = DataSource(
                                        category=f"{category}.{key}",
                                        key=sub_key,
                                        name=sub_config.get('name', sub_key),
                                        url=sub_config.get('url', ''),
                                        type=sub_config.get('type', 'unknown'),
                                        priority=sub_config.get('priority', 'low'),
                                        config=sub_config
                                    )
                                    self.sources[f"{category}.{key}.{sub_key}"] = source

            logger.info(f"Loaded {len(self.sources)} data sources")

        except Exception as e:
            logger.error(f"Error loading sources: {e}")

    def get_sources_by_priority(self, priority: str) -> List[DataSource]:
        """Get all sources with specific priority"""
        return [s for s in self.sources.values() if s.priority == priority]

    def get_sources_by_category(self, category: str) -> List[DataSource]:
        """Get all sources in a category"""
        return [s for s in self.sources.values() if s.category.startswith(category)]

    def get_api_sources(self) -> List[DataSource]:
        """Get all API sources"""
        return [s for s in self.sources.values() if s.is_api]

    def get_scraper_sources(self) -> List[DataSource]:
        """Get all scraper sources"""
        return [s for s in self.sources.values() if s.is_scraper]

    async def initialize_collectors(self):
        """Initialize all data collectors (APIs and scrapers)"""

        # Initialize API clients
        api_sources = self.get_api_sources()
        for source in api_sources:
            try:
                client = await self._create_api_client(source)
                if client:
                    self.api_clients[source.key] = client
                    logger.info(f"Initialized API client: {source.name}")
            except Exception as e:
                logger.error(f"Failed to initialize API {source.name}: {e}")

        # Initialize scrapers
        scraper_sources = self.get_scraper_sources()
        for source in scraper_sources:
            try:
                scraper = await self._create_scraper(source)
                if scraper:
                    self.scrapers[source.key] = scraper
                    logger.info(f"Initialized scraper: {source.name}")
            except Exception as e:
                logger.error(f"Failed to initialize scraper {source.name}: {e}")

    async def _create_api_client(self, source: DataSource):
        """Dynamically create API client for source"""
        # Map source keys to client classes
        client_map = {
            'dane': 'backend.api_clients.clients.dane_client.DANEClient',
            'banco_republica': 'backend.api_clients.clients.banrep_client.BancoRepublicaClient',
            'datos_gov': 'backend.api_clients.clients.datos_gov_client.DatosGovClient',
            'secop': 'backend.api_clients.clients.secop_client.SECOPClient',
        }

        if source.key in client_map:
            try:
                module_path, class_name = client_map[source.key].rsplit('.', 1)
                module = importlib.import_module(module_path)
                client_class = getattr(module, class_name)
                return client_class(source.config)
            except Exception as e:
                logger.error(f"Error creating API client for {source.key}: {e}")

        return None

    async def _create_scraper(self, source: DataSource):
        """Dynamically create scraper for source"""
        # Map source keys to scraper classes
        scraper_map = {
            'el_tiempo': 'backend.scrapers.sources.media.el_tiempo.ElTiempoScraper',
            'el_espectador': 'backend.scrapers.sources.media.el_espectador.ElEspectadorScraper',
            'semana': 'backend.scrapers.sources.media.semana.SemanaScraper',
            'la_republica': 'backend.scrapers.sources.media.la_republica.LaRepublicaScraper',
        }

        if source.key in scraper_map:
            try:
                module_path, class_name = scraper_map[source.key].rsplit('.', 1)
                module = importlib.import_module(module_path)
                scraper_class = getattr(module, class_name)
                return scraper_class(source.config)
            except Exception as e:
                logger.warning(f"Scraper not yet implemented for {source.key}: {e}")

        return None

    def schedule_all_sources(self):
        """Schedule all sources for periodic collection"""

        # Schedule high priority sources
        high_priority = self.get_sources_by_priority('high')
        for source in high_priority:
            self._schedule_source(source)

        # Schedule medium priority sources
        medium_priority = self.get_sources_by_priority('medium')
        for source in medium_priority:
            self._schedule_source(source)

        # Start scheduler
        self.scheduler.start()
        logger.info(f"Scheduled {len(high_priority) + len(medium_priority)} sources")

    def _schedule_source(self, source: DataSource):
        """Schedule a single source for collection"""
        interval = source.update_interval

        if source.is_api and source.key in self.api_clients:
            self.scheduler.add_job(
                self._collect_from_api,
                trigger=IntervalTrigger(minutes=interval),
                args=[source],
                id=f"api_{source.key}",
                name=f"Collect from {source.name} API"
            )
        elif source.is_scraper and source.key in self.scrapers:
            self.scheduler.add_job(
                self._collect_from_scraper,
                trigger=IntervalTrigger(minutes=interval),
                args=[source],
                id=f"scraper_{source.key}",
                name=f"Scrape {source.name}"
            )

    async def _collect_from_api(self, source: DataSource):
        """Collect data from API source"""
        try:
            client = self.api_clients.get(source.key)
            if client:
                data = await client.fetch_latest()
                logger.info(f"Collected {len(data)} items from {source.name} API")
                # Process and store data
                await self._process_data(data, source)
        except Exception as e:
            logger.error(f"Error collecting from {source.name} API: {e}")

    async def _collect_from_scraper(self, source: DataSource):
        """Collect data from scraper source"""
        try:
            scraper = self.scrapers.get(source.key)
            if scraper:
                documents = scraper.scrape_batch(limit=10)
                logger.info(f"Scraped {len(documents)} documents from {source.name}")
                # Process and store documents
                await self._process_documents(documents, source)
        except Exception as e:
            logger.error(f"Error scraping {source.name}: {e}")

    async def _process_data(self, data: List[Dict], source: DataSource):
        """
        Process and store API data to database

        Args:
            data: List of API response dictionaries
            source: DataSource configuration

        Features:
            - Async batch processing for performance
            - Data validation and quality checks
            - Intelligence alert generation
            - Error handling with logging
        """
        if not data:
            logger.info(f"No data to process from {source.name}")
            return

        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        from backend.app.database.models import IntelligenceAlert

        try:
            # Create database session
            # TODO: Inject database configuration from settings
            engine = create_engine('sqlite:///openlearn.db', echo=False)
            Session = sessionmaker(bind=engine)
            session = Session()

            processed_count = 0
            alert_count = 0

            # Process each data item
            for item in data:
                try:
                    # Validate required fields
                    if not self._validate_api_data(item):
                        logger.warning(f"Invalid data structure from {source.name}: {item}")
                        continue

                    # Extract data and metadata
                    source_name = item.get('source', source.name)
                    data_content = item.get('data', {})
                    metadata = item.get('metadata', {})
                    extracted_at = item.get('extracted_at')

                    # Check for alert conditions
                    alerts = self._check_data_alerts(data_content, source)

                    # Create intelligence alerts if needed
                    for alert_info in alerts:
                        alert = IntelligenceAlert(
                            alert_type=alert_info['type'],
                            title=alert_info['title'],
                            description=alert_info['description'],
                            severity=alert_info['severity'],
                            keywords=alert_info.get('keywords', []),
                            entities=[source_name],
                            triggered_by_content_ids=[],
                            matched_patterns={'indicator': alert_info.get('indicator')},
                            status='active'
                        )
                        session.add(alert)
                        alert_count += 1

                    # TODO: Store structured API data
                    # For now, we create alerts and log successful processing
                    # Future: Create dedicated tables for economic indicators, etc.

                    processed_count += 1

                except Exception as e:
                    logger.error(f"Error processing data item from {source.name}: {e}")
                    continue

            # Commit all changes
            session.commit()
            logger.info(
                f"Processed {processed_count}/{len(data)} items from {source.name}, "
                f"created {alert_count} alerts"
            )

        except Exception as e:
            logger.error(f"Error in _process_data for {source.name}: {e}")
            if 'session' in locals():
                session.rollback()
        finally:
            if 'session' in locals():
                session.close()

    async def _process_documents(self, documents: List, source: DataSource):
        """
        Process and store scraped documents to database

        Args:
            documents: List of scraped document dictionaries
            source: DataSource configuration

        Features:
            - Async batch processing
            - Duplicate detection via content_hash
            - Difficulty score calculation for language learning
            - Colombian entity extraction
            - Content analysis generation
        """
        if not documents:
            logger.info(f"No documents to process from {source.name}")
            return

        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        from backend.app.database.models import ScrapedContent, ContentAnalysis

        try:
            # Create database session
            engine = create_engine('sqlite:///openlearn.db', echo=False)
            Session = sessionmaker(bind=engine)
            session = Session()

            stored_count = 0
            duplicate_count = 0

            # Process documents in batches for performance
            for doc in documents:
                try:
                    # Validate required fields
                    if not self._validate_document_data(doc):
                        logger.warning(f"Invalid document structure from {source.name}")
                        continue

                    # Check for duplicates using content_hash
                    content_hash = doc.get('content_hash')
                    if content_hash:
                        exists = session.query(ScrapedContent).filter_by(
                            content_hash=content_hash
                        ).first()
                        if exists:
                            duplicate_count += 1
                            continue

                    # Also check URL duplicates
                    source_url = doc.get('source_url')
                    if source_url:
                        exists = session.query(ScrapedContent).filter_by(
                            source_url=source_url
                        ).first()
                        if exists:
                            duplicate_count += 1
                            continue

                    # Calculate difficulty score for language learning
                    difficulty_score = self._calculate_difficulty_score(
                        doc.get('content', '')
                    )

                    # Extract Colombian entities
                    colombian_entities = self._extract_colombian_entities(
                        doc.get('content', ''),
                        doc.get('title', '')
                    )

                    # Parse published date
                    published_date = None
                    if doc.get('published_date'):
                        try:
                            if isinstance(doc['published_date'], str):
                                published_date = datetime.fromisoformat(
                                    doc['published_date'].replace('Z', '+00:00')
                                )
                            else:
                                published_date = doc['published_date']
                        except (ValueError, TypeError):
                            pass

                    # Create ScrapedContent record
                    content = ScrapedContent(
                        source=doc.get('source', source.name),
                        source_url=source_url or '',
                        category=doc.get('category', source.category),
                        title=doc.get('title', ''),
                        subtitle=doc.get('subtitle'),
                        content=doc.get('content', ''),
                        author=doc.get('author'),
                        word_count=doc.get('word_count') or len(doc.get('content', '').split()),
                        published_date=published_date,
                        content_hash=content_hash,
                        colombian_entities=colombian_entities,
                        tags=doc.get('tags', []),
                        extra_metadata=doc.get('metadata', {}),
                        difficulty_score=difficulty_score,
                        is_paywall=doc.get('is_paywall', False)
                    )

                    session.add(content)
                    session.flush()  # Get content.id

                    # Create ContentAnalysis record
                    analysis = self._analyze_content(doc.get('content', ''))
                    if analysis:
                        content_analysis = ContentAnalysis(
                            content_id=content.id,
                            entities=analysis.get('entities', {}),
                            sentiment_score=analysis.get('sentiment_score'),
                            sentiment_label=analysis.get('sentiment_label'),
                            key_phrases=analysis.get('key_phrases', []),
                            topics=analysis.get('topics', []),
                            summary=analysis.get('summary'),
                            colombian_slang=analysis.get('colombian_slang', []),
                            model_version='1.0.0'
                        )
                        session.add(content_analysis)

                    stored_count += 1

                except Exception as e:
                    logger.error(f"Error processing document from {source.name}: {e}")
                    continue

            # Commit all changes
            session.commit()
            logger.info(
                f"Processed {stored_count} new documents from {source.name}, "
                f"skipped {duplicate_count} duplicates"
            )

        except Exception as e:
            logger.error(f"Error in _process_documents for {source.name}: {e}")
            if 'session' in locals():
                session.rollback()
        finally:
            if 'session' in locals():
                session.close()

    def _validate_api_data(self, data: Dict) -> bool:
        """
        Validate API data structure

        Args:
            data: API data dictionary

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            return False

        # Must have either 'source' or 'data' field
        return 'source' in data or 'data' in data

    def _validate_document_data(self, doc: Dict) -> bool:
        """
        Validate document data structure

        Args:
            doc: Document dictionary

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(doc, dict):
            return False

        # Must have title and content at minimum
        required = ['title', 'content']
        return all(field in doc for field in required)

    def _check_data_alerts(self, data: Dict, source: DataSource) -> List[Dict]:
        """
        Check for alert conditions in API data

        Args:
            data: Data content to check
            source: Data source

        Returns:
            List of alert dictionaries
        """
        alerts = []

        # Economic indicator thresholds
        thresholds = {
            'ipc_monthly_change': 1.0,  # Inflation > 1% monthly
            'unemployment_rate': 15.0,  # Unemployment > 15%
            'gdp_quarterly_change': -2.0  # GDP contraction > 2%
        }

        # Check inflation
        if 'variacion_mensual' in data:
            if data['variacion_mensual'] > thresholds['ipc_monthly_change']:
                alerts.append({
                    'type': 'economic_indicator',
                    'title': 'High Inflation Alert',
                    'description': f"Monthly inflation of {data['variacion_mensual']}% exceeds threshold",
                    'severity': 'high',
                    'indicator': 'inflation',
                    'keywords': ['inflación', 'IPC', 'economía']
                })

        # Check unemployment
        if 'tasa_desempleo' in data:
            if data['tasa_desempleo'] > thresholds['unemployment_rate']:
                alerts.append({
                    'type': 'economic_indicator',
                    'title': 'High Unemployment Alert',
                    'description': f"Unemployment rate of {data['tasa_desempleo']}% exceeds threshold",
                    'severity': 'high',
                    'indicator': 'unemployment',
                    'keywords': ['desempleo', 'empleo', 'trabajo']
                })

        return alerts

    def _calculate_difficulty_score(self, text: str) -> float:
        """
        Calculate reading difficulty score for language learning

        Args:
            text: Content text

        Returns:
            Difficulty score from 1.0 (easy) to 5.0 (difficult)
        """
        if not text:
            return 2.5

        # Basic difficulty calculation based on:
        # - Average word length
        # - Average sentence length
        # - Vocabulary complexity

        words = text.split()
        if not words:
            return 2.5

        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Approximate sentence count
        sentence_endings = text.count('.') + text.count('!') + text.count('?')
        sentence_endings = max(sentence_endings, 1)
        avg_sentence_length = len(words) / sentence_endings

        # Calculate score (simplified algorithm)
        # Longer words and sentences = higher difficulty
        difficulty = 1.0

        if avg_word_length > 6:
            difficulty += 1.0
        if avg_word_length > 8:
            difficulty += 0.5

        if avg_sentence_length > 20:
            difficulty += 1.0
        if avg_sentence_length > 30:
            difficulty += 0.5

        # Cap at 5.0
        return min(difficulty, 5.0)

    def _extract_colombian_entities(self, content: str, title: str = '') -> Dict:
        """
        Extract Colombian-specific entities from text

        Args:
            content: Document content
            title: Document title

        Returns:
            Dictionary of extracted entities
        """
        entities = {
            'institutions': [],
            'locations': [],
            'people': [],
            'organizations': []
        }

        combined_text = f"{title} {content}".lower()

        # Colombian institutions
        institutions = [
            'congreso', 'senado', 'cámara de representantes',
            'dane', 'banco de la república', 'corte constitucional',
            'fiscalía', 'procuraduría', 'contraloría'
        ]
        for inst in institutions:
            if inst in combined_text:
                entities['institutions'].append(inst.title())

        # Major Colombian cities
        cities = [
            'bogotá', 'medellín', 'cali', 'barranquilla',
            'cartagena', 'cúcuta', 'bucaramanga', 'pereira',
            'manizales', 'ibagué', 'santa marta'
        ]
        for city in cities:
            if city in combined_text:
                entities['locations'].append(city.title())

        # Colombian regions/departments
        departments = [
            'antioquia', 'cundinamarca', 'valle del cauca',
            'atlántico', 'santander', 'bolívar'
        ]
        for dept in departments:
            if dept in combined_text:
                entities['locations'].append(dept.title())

        return entities

    def _analyze_content(self, content: str) -> Optional[Dict]:
        """
        Perform basic content analysis

        Args:
            content: Document content

        Returns:
            Analysis results dictionary or None
        """
        if not content:
            return None

        # Basic sentiment analysis (simplified)
        positive_words = [
            'éxito', 'mejor', 'ganancia', 'crecimiento', 'avance',
            'positivo', 'beneficio', 'progreso', 'bueno', 'excelente'
        ]
        negative_words = [
            'crisis', 'problema', 'caída', 'pérdida', 'preocupación',
            'negativo', 'riesgo', 'fracaso', 'malo', 'difícil'
        ]

        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)

        total = positive_count + negative_count
        if total > 0:
            sentiment_score = (positive_count - negative_count) / total
        else:
            sentiment_score = 0.0

        # Determine sentiment label
        if sentiment_score > 0.2:
            sentiment_label = 'positive'
        elif sentiment_score < -0.2:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'

        # Extract key phrases (simplified - just common Colombian terms)
        colombian_slang = []
        slang_terms = [
            'parce', 'chimba', 'bacano', 'chévere', 'teso',
            'vaina', 'parcero', 'pola', 'guaro', 'rumba'
        ]
        for term in slang_terms:
            if term in content_lower:
                colombian_slang.append(term)

        # Generate simple summary (first 200 characters)
        summary = content[:200] + '...' if len(content) > 200 else content

        return {
            'entities': {},  # TODO: Implement NER
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'key_phrases': [],  # TODO: Implement key phrase extraction
            'topics': [],  # TODO: Implement topic modeling
            'summary': summary,
            'colombian_slang': colombian_slang
        }

    def get_status(self) -> Dict[str, Any]:
        """Get status of all sources"""
        return {
            'total_sources': len(self.sources),
            'api_sources': len(self.get_api_sources()),
            'scraper_sources': len(self.get_scraper_sources()),
            'active_apis': len(self.api_clients),
            'active_scrapers': len(self.scrapers),
            'scheduled_jobs': len(self.scheduler.get_jobs()),
            'sources_by_priority': {
                'high': len(self.get_sources_by_priority('high')),
                'medium': len(self.get_sources_by_priority('medium')),
                'low': len(self.get_sources_by_priority('low'))
            }
        }

    async def test_source(self, source_key: str) -> Dict[str, Any]:
        """Test a specific source"""
        source = self.sources.get(source_key)
        if not source:
            return {'error': f'Source {source_key} not found'}

        result = {
            'source': source.name,
            'type': 'API' if source.is_api else 'Scraper',
            'status': 'unknown',
            'data': None,
            'error': None
        }

        try:
            if source.is_api:
                client = await self._create_api_client(source)
                if client:
                    data = await client.test_connection()
                    result['status'] = 'success'
                    result['data'] = data
            elif source.is_scraper:
                scraper = await self._create_scraper(source)
                if scraper:
                    docs = scraper.scrape_batch(limit=1)
                    result['status'] = 'success'
                    result['data'] = f"Scraped {len(docs)} documents"
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result