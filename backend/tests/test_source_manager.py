"""
Test suite for the Source Manager

Tests orchestration of all 42+ data sources including APIs, scrapers,
scheduling, data processing, and error handling.
"""

import pytest
import asyncio
import tempfile
import yaml
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from backend.core.source_manager import SourceManager, DataSource
from backend.api_clients.clients.dane_client import DANEClient
from backend.scrapers.sources.media.el_tiempo import ElTiempoScraper


class TestDataSource:
    """Test DataSource configuration class"""

    @pytest.fixture
    def sample_api_source(self):
        """Sample API data source"""
        return DataSource(
            category='government',
            key='dane',
            name='DANE - Estadísticas',
            url='https://dane.gov.co',
            type='statistics',
            priority='high',
            config={
                'api_endpoint': 'https://dane.gov.co/api',
                'rate_limit': '10/minute',
                'update_frequency': 'daily'
            }
        )

    @pytest.fixture
    def sample_scraper_source(self):
        """Sample scraper data source"""
        return DataSource(
            category='media.national',
            key='el_tiempo',
            name='El Tiempo',
            url='https://eltiempo.com',
            type='news',
            priority='high',
            config={
                'scraping_interval': 30,
                'selectors': {
                    'article': 'article.article-container',
                    'title': 'h1.titulo'
                }
            }
        )

    def test_data_source_properties(self, sample_api_source, sample_scraper_source):
        """Test DataSource property detection"""
        # API source
        assert sample_api_source.is_api is True
        assert sample_api_source.is_scraper is False
        assert sample_api_source.update_interval == 1440  # daily = 1440 minutes

        # Scraper source
        assert sample_scraper_source.is_api is False
        assert sample_scraper_source.is_scraper is True
        assert sample_scraper_source.update_interval == 30

    def test_update_interval_calculation(self):
        """Test update interval calculation for different frequencies"""
        # Hourly frequency
        hourly_source = DataSource(
            category='test', key='test', name='Test', url='test.com',
            type='test', priority='medium',
            config={'update_frequency': 'hourly'}
        )
        assert hourly_source.update_interval == 60

        # Weekly frequency
        weekly_source = DataSource(
            category='test', key='test', name='Test', url='test.com',
            type='test', priority='medium',
            config={'update_frequency': 'weekly'}
        )
        assert weekly_source.update_interval == 10080

        # Custom scraping interval
        custom_source = DataSource(
            category='test', key='test', name='Test', url='test.com',
            type='test', priority='medium',
            config={'scraping_interval': 120}
        )
        assert custom_source.update_interval == 120


class TestSourceManager:
    """Test SourceManager orchestration"""

    @pytest.fixture
    def source_manager(self, temp_config_file):
        """Create SourceManager instance with test config"""
        return SourceManager(config_path=temp_config_file)

    @pytest.fixture
    def mock_source_manager(self, temp_config_file):
        """Create mocked SourceManager instance"""
        manager = SourceManager(config_path=temp_config_file)

        # Mock scheduler
        manager.scheduler = Mock()
        manager.scheduler.add_job = Mock()
        manager.scheduler.start = Mock()
        manager.scheduler.get_jobs = Mock(return_value=[])

        return manager

    def test_initialization(self, source_manager):
        """Test SourceManager initialization"""
        assert source_manager.config_path is not None
        assert isinstance(source_manager.sources, dict)
        assert source_manager.scheduler is not None
        assert isinstance(source_manager.api_clients, dict)
        assert isinstance(source_manager.scrapers, dict)

    def test_load_sources(self, source_manager, test_sources_config):
        """Test loading sources from configuration"""
        # Sources should be loaded from config
        assert len(source_manager.sources) > 0

        # Check specific sources
        assert 'government.dane' in source_manager.sources
        assert 'media.national.el_tiempo' in source_manager.sources

        dane_source = source_manager.sources['government.dane']
        assert dane_source.name == 'DANE - Test'
        assert dane_source.priority == 'high'
        assert dane_source.is_api is True

    def test_get_sources_by_priority(self, source_manager):
        """Test filtering sources by priority"""
        high_priority = source_manager.get_sources_by_priority('high')
        medium_priority = source_manager.get_sources_by_priority('medium')
        low_priority = source_manager.get_sources_by_priority('low')

        assert isinstance(high_priority, list)
        assert isinstance(medium_priority, list)
        assert isinstance(low_priority, list)

        # All high priority sources should have priority='high'
        for source in high_priority:
            assert source.priority == 'high'

    def test_get_sources_by_category(self, source_manager):
        """Test filtering sources by category"""
        government_sources = source_manager.get_sources_by_category('government')
        media_sources = source_manager.get_sources_by_category('media')

        assert isinstance(government_sources, list)
        assert isinstance(media_sources, list)

        # All government sources should start with 'government'
        for source in government_sources:
            assert source.category.startswith('government')

    def test_get_api_sources(self, source_manager):
        """Test filtering API sources"""
        api_sources = source_manager.get_api_sources()

        assert isinstance(api_sources, list)
        for source in api_sources:
            assert source.is_api is True

    def test_get_scraper_sources(self, source_manager):
        """Test filtering scraper sources"""
        scraper_sources = source_manager.get_scraper_sources()

        assert isinstance(scraper_sources, list)
        for source in scraper_sources:
            assert source.is_scraper is True

    @pytest.mark.asyncio
    async def test_create_api_client(self, source_manager):
        """Test API client creation"""
        dane_source = DataSource(
            category='government',
            key='dane',
            name='DANE Test',
            url='https://test.dane.gov.co',
            type='statistics',
            priority='high',
            config={'api_endpoint': 'https://test.dane.gov.co/api'}
        )

        with patch('backend.core.source_manager.importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_client_class = Mock()
            mock_module.DANEClient = mock_client_class
            mock_import.return_value = mock_module

            client = await source_manager._create_api_client(dane_source)

            # Should attempt to create client
            mock_import.assert_called()
            mock_client_class.assert_called_with(dane_source.config)

    @pytest.mark.asyncio
    async def test_create_scraper(self, source_manager):
        """Test scraper creation"""
        el_tiempo_source = DataSource(
            category='media.national',
            key='el_tiempo',
            name='El Tiempo Test',
            url='https://test.eltiempo.com',
            type='news',
            priority='high',
            config={'scraping_interval': 30}
        )

        with patch('backend.core.source_manager.importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_scraper_class = Mock()
            mock_module.ElTiempoScraper = mock_scraper_class
            mock_import.return_value = mock_module

            scraper = await source_manager._create_scraper(el_tiempo_source)

            # Should attempt to create scraper
            mock_import.assert_called()
            mock_scraper_class.assert_called_with(el_tiempo_source.config)

    @pytest.mark.asyncio
    async def test_initialize_collectors(self, mock_source_manager):
        """Test initialization of all data collectors"""
        # Mock some sources
        api_source = Mock()
        api_source.is_api = True
        api_source.key = 'test_api'
        api_source.name = 'Test API'

        scraper_source = Mock()
        scraper_source.is_scraper = True
        scraper_source.key = 'test_scraper'
        scraper_source.name = 'Test Scraper'

        mock_source_manager.get_api_sources = Mock(return_value=[api_source])
        mock_source_manager.get_scraper_sources = Mock(return_value=[scraper_source])
        mock_source_manager._create_api_client = AsyncMock(return_value=Mock())
        mock_source_manager._create_scraper = AsyncMock(return_value=Mock())

        await mock_source_manager.initialize_collectors()

        # Should initialize both APIs and scrapers
        mock_source_manager._create_api_client.assert_called_once_with(api_source)
        mock_source_manager._create_scraper.assert_called_once_with(scraper_source)

    def test_schedule_all_sources(self, mock_source_manager):
        """Test scheduling all sources"""
        # Mock high priority sources
        high_source = Mock()
        high_source.priority = 'high'
        high_source.key = 'high_test'
        high_source.is_api = True
        high_source.update_interval = 60

        medium_source = Mock()
        medium_source.priority = 'medium'
        medium_source.key = 'medium_test'
        medium_source.is_scraper = True
        medium_source.update_interval = 120

        mock_source_manager.get_sources_by_priority = Mock(side_effect=lambda p:
            [high_source] if p == 'high' else [medium_source] if p == 'medium' else []
        )
        mock_source_manager.api_clients = {'high_test': Mock()}
        mock_source_manager.scrapers = {'medium_test': Mock()}

        mock_source_manager.schedule_all_sources()

        # Should start scheduler
        mock_source_manager.scheduler.start.assert_called_once()

        # Should schedule jobs for high and medium priority sources
        assert mock_source_manager.scheduler.add_job.call_count >= 2

    @pytest.mark.asyncio
    async def test_collect_from_api(self, mock_source_manager):
        """Test collecting data from API source"""
        # Mock API client
        mock_client = AsyncMock()
        mock_client.fetch_latest = AsyncMock(return_value=[{'test': 'data'}])

        mock_source_manager.api_clients = {'test_api': mock_client}
        mock_source_manager._process_data = AsyncMock()

        # Mock source
        source = Mock()
        source.key = 'test_api'
        source.name = 'Test API'

        await mock_source_manager._collect_from_api(source)

        # Should fetch data and process it
        mock_client.fetch_latest.assert_called_once()
        mock_source_manager._process_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_from_scraper(self, mock_source_manager):
        """Test collecting data from scraper source"""
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape_batch = Mock(return_value=[{'title': 'Test Article'}])

        mock_source_manager.scrapers = {'test_scraper': mock_scraper}
        mock_source_manager._process_documents = AsyncMock()

        # Mock source
        source = Mock()
        source.key = 'test_scraper'
        source.name = 'Test Scraper'

        await mock_source_manager._collect_from_scraper(source)

        # Should scrape data and process it
        mock_scraper.scrape_batch.assert_called_once_with(limit=10)
        mock_source_manager._process_documents.assert_called_once()

    def test_get_status(self, mock_source_manager):
        """Test getting manager status"""
        # Mock sources
        mock_source_manager.sources = {
            'api1': Mock(is_api=True, is_scraper=False, priority='high'),
            'api2': Mock(is_api=True, is_scraper=False, priority='medium'),
            'scraper1': Mock(is_api=False, is_scraper=True, priority='high'),
            'scraper2': Mock(is_api=False, is_scraper=True, priority='low')
        }

        mock_source_manager.api_clients = {'api1': Mock()}
        mock_source_manager.scrapers = {'scraper1': Mock()}

        status = mock_source_manager.get_status()

        assert status['total_sources'] == 4
        assert status['api_sources'] == 2
        assert status['scraper_sources'] == 2
        assert status['active_apis'] == 1
        assert status['active_scrapers'] == 1
        assert status['sources_by_priority']['high'] == 2
        assert status['sources_by_priority']['medium'] == 1
        assert status['sources_by_priority']['low'] == 1

    @pytest.mark.asyncio
    async def test_test_source_api(self, mock_source_manager):
        """Test testing an API source"""
        # Mock API source
        api_source = Mock()
        api_source.is_api = True
        api_source.is_scraper = False
        api_source.name = 'Test API'

        mock_source_manager.sources = {'test.api': api_source}

        # Mock client creation and testing
        mock_client = AsyncMock()
        mock_client.test_connection = AsyncMock(return_value={'status': 'ok'})
        mock_source_manager._create_api_client = AsyncMock(return_value=mock_client)

        result = await mock_source_manager.test_source('test.api')

        assert result['source'] == 'Test API'
        assert result['type'] == 'API'
        assert result['status'] == 'success'
        assert result['data'] == {'status': 'ok'}

    @pytest.mark.asyncio
    async def test_test_source_scraper(self, mock_source_manager):
        """Test testing a scraper source"""
        # Mock scraper source
        scraper_source = Mock()
        scraper_source.is_api = False
        scraper_source.is_scraper = True
        scraper_source.name = 'Test Scraper'

        mock_source_manager.sources = {'test.scraper': scraper_source}

        # Mock scraper creation and testing
        mock_scraper = Mock()
        mock_scraper.scrape_batch = Mock(return_value=[{'title': 'Test'}])
        mock_source_manager._create_scraper = AsyncMock(return_value=mock_scraper)

        result = await mock_source_manager.test_source('test.scraper')

        assert result['source'] == 'Test Scraper'
        assert result['type'] == 'Scraper'
        assert result['status'] == 'success'
        assert 'Scraped 1 documents' in result['data']

    @pytest.mark.asyncio
    async def test_test_source_not_found(self, mock_source_manager):
        """Test testing a non-existent source"""
        mock_source_manager.sources = {}

        result = await mock_source_manager.test_source('nonexistent')

        assert 'error' in result
        assert 'not found' in result['error']

    @pytest.mark.asyncio
    async def test_error_handling_api_collection(self, mock_source_manager):
        """Test error handling during API data collection"""
        # Mock failing API client
        mock_client = AsyncMock()
        mock_client.fetch_latest = AsyncMock(side_effect=Exception("API Error"))

        mock_source_manager.api_clients = {'failing_api': mock_client}

        source = Mock()
        source.key = 'failing_api'
        source.name = 'Failing API'

        # Should not raise exception
        await mock_source_manager._collect_from_api(source)

    @pytest.mark.asyncio
    async def test_error_handling_scraper_collection(self, mock_source_manager):
        """Test error handling during scraper data collection"""
        # Mock failing scraper
        mock_scraper = Mock()
        mock_scraper.scrape_batch = Mock(side_effect=Exception("Scraper Error"))

        mock_source_manager.scrapers = {'failing_scraper': mock_scraper}

        source = Mock()
        source.key = 'failing_scraper'
        source.name = 'Failing Scraper'

        # Should not raise exception
        await mock_source_manager._collect_from_scraper(source)


class TestSourceManagerIntegration:
    """Integration tests for SourceManager with real components"""

    @pytest.fixture
    def integration_config(self):
        """Configuration for integration tests"""
        return {
            'government': {
                'dane': {
                    'name': 'DANE Integration Test',
                    'url': 'https://test.dane.gov.co',
                    'api_endpoint': 'https://test.dane.gov.co/api',
                    'type': 'statistics',
                    'priority': 'high',
                    'rate_limit': '10/minute',
                    'auth_type': 'api_key',
                    'update_frequency': 'daily'
                }
            },
            'media': {
                'national': {
                    'el_tiempo': {
                        'name': 'El Tiempo Integration Test',
                        'url': 'https://test.eltiempo.com',
                        'type': 'news',
                        'priority': 'high',
                        'scraping_interval': 30,
                        'selectors': {
                            'article': 'article.article-container',
                            'title': 'h1.titulo',
                            'content': 'div.articulo-contenido'
                        }
                    }
                }
            }
        }

    @pytest.fixture
    def integration_source_manager(self, integration_config):
        """Create SourceManager with integration config"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(integration_config, f)
            config_path = f.name

        return SourceManager(config_path=config_path)

    @pytest.mark.asyncio
    async def test_full_initialization_cycle(self, integration_source_manager):
        """Test full initialization cycle with all components"""
        # Load sources
        assert len(integration_source_manager.sources) == 2

        # Mock the import and client/scraper creation
        with patch('backend.core.source_manager.importlib.import_module') as mock_import:
            # Mock successful imports
            mock_module = Mock()
            mock_dane_client = Mock()
            mock_el_tiempo_scraper = Mock()

            mock_module.DANEClient = mock_dane_client
            mock_module.ElTiempoScraper = mock_el_tiempo_scraper
            mock_import.return_value = mock_module

            # Initialize collectors
            await integration_source_manager.initialize_collectors()

    @pytest.mark.asyncio
    async def test_concurrent_source_operations(self, integration_source_manager):
        """Test concurrent operations across multiple sources"""
        # Mock multiple sources
        sources = list(integration_source_manager.sources.values())

        # Test concurrent source testing
        tasks = []
        for source_key in integration_source_manager.sources.keys():
            tasks.append(integration_source_manager.test_source(source_key))

        # Should handle concurrent operations
        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert len(results) == len(sources)
        # Results should be either dicts or exceptions
        assert all(isinstance(r, (dict, Exception)) for r in results)

    def test_configuration_validation(self, integration_source_manager):
        """Test configuration validation and error handling"""
        # Invalid configuration should be handled gracefully
        invalid_config = {
            'invalid_category': {
                'invalid_source': 'not_a_dict'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            invalid_config_path = f.name

        # Should not crash on invalid config
        manager = SourceManager(config_path=invalid_config_path)
        assert isinstance(manager.sources, dict)

    @pytest.mark.asyncio
    async def test_scheduler_integration(self, integration_source_manager):
        """Test scheduler integration with real APScheduler"""
        # Mock some initialized collectors
        integration_source_manager.api_clients = {'dane': Mock()}
        integration_source_manager.scrapers = {'el_tiempo': Mock()}

        # Schedule sources
        integration_source_manager.schedule_all_sources()

        # Scheduler should be started
        assert integration_source_manager.scheduler.running is True

        # Clean up
        integration_source_manager.scheduler.shutdown()


class TestSourceManagerPerformance:
    """Performance tests for SourceManager"""

    @pytest.mark.asyncio
    async def test_large_number_of_sources(self):
        """Test performance with large number of sources"""
        # Create config with many sources
        large_config = {}

        # Generate 100 test sources
        for i in range(100):
            category = f'category_{i // 10}'
            if category not in large_config:
                large_config[category] = {}

            large_config[category][f'source_{i}'] = {
                'name': f'Test Source {i}',
                'url': f'https://test{i}.com',
                'type': 'test',
                'priority': 'medium',
                'scraping_interval': 60
            }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(large_config, f)
            config_path = f.name

        manager = SourceManager(config_path=config_path)

        # Should handle large number of sources
        assert len(manager.sources) == 100

        # Test filtering performance
        start_time = datetime.now()
        medium_sources = manager.get_sources_by_priority('medium')
        end_time = datetime.now()

        assert len(medium_sources) == 100
        # Should be fast (< 1 second)
        assert (end_time - start_time).total_seconds() < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_collector_initialization(self, integration_source_manager):
        """Test concurrent initialization of many collectors"""
        # Mock many sources
        sources = []
        for i in range(20):
            source = Mock()
            source.key = f'source_{i}'
            source.name = f'Source {i}'
            source.is_api = i % 2 == 0  # Alternate API/scraper
            source.is_scraper = i % 2 == 1
            sources.append(source)

        integration_source_manager.get_api_sources = Mock(return_value=[s for s in sources if s.is_api])
        integration_source_manager.get_scraper_sources = Mock(return_value=[s for s in sources if s.is_scraper])

        # Mock creation methods
        integration_source_manager._create_api_client = AsyncMock(return_value=Mock())
        integration_source_manager._create_scraper = AsyncMock(return_value=Mock())

        start_time = datetime.now()
        await integration_source_manager.initialize_collectors()
        end_time = datetime.now()

        # Should initialize in reasonable time
        assert (end_time - start_time).total_seconds() < 5.0

    def test_memory_usage_with_many_sources(self):
        """Test memory usage with large configuration"""
        # This would be a more comprehensive test in a real scenario
        # For now, just verify it doesn't crash

        large_config = {}
        for i in range(1000):
            large_config[f'source_{i}'] = {
                'name': f'Source {i}',
                'url': f'https://test{i}.com',
                'type': 'test',
                'priority': 'low',
                'config': {'data': 'x' * 1000}  # Add some bulk
            }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(large_config, f)
            config_path = f.name

        # Should handle large config without memory issues
        manager = SourceManager(config_path=config_path)
        assert len(manager.sources) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])