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
        """Process and store API data"""
        # TODO: Implement data processing pipeline
        pass

    async def _process_documents(self, documents: List, source: DataSource):
        """Process and store scraped documents"""
        # TODO: Implement document processing pipeline
        pass

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