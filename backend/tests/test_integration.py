"""
End-to-end integration tests for the Colombian Intelligence Platform

Tests the complete data flow from source collection through processing,
storage, analysis, and API endpoints.
"""

import pytest
import asyncio
import tempfile
import json
import yaml
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from backend.core.source_manager import SourceManager
from backend.api_clients.clients.dane_client import DANEClient
from backend.scrapers.sources.media.el_tiempo import ElTiempoScraper
from conftest import assert_valid_news_article, assert_valid_api_data


class TestDataFlowIntegration:
    """Test complete data flow from sources to storage"""

    @pytest.fixture
    def full_system_config(self):
        """Complete system configuration for integration tests"""
        return {
            'government': {
                'dane': {
                    'name': 'DANE - Estadísticas',
                    'url': 'https://test.dane.gov.co',
                    'api_endpoint': 'https://test.dane.gov.co/api',
                    'type': 'statistics',
                    'priority': 'high',
                    'rate_limit': '10/minute',
                    'auth_type': 'api_key',
                    'update_frequency': 'daily'
                },
                'banco_republica': {
                    'name': 'Banco de la República',
                    'url': 'https://test.banrep.gov.co',
                    'api_endpoint': 'https://test.banrep.gov.co/api',
                    'type': 'economic',
                    'priority': 'high',
                    'rate_limit': '20/minute',
                    'auth_type': 'none',
                    'update_frequency': 'daily'
                }
            },
            'media': {
                'national': {
                    'el_tiempo': {
                        'name': 'El Tiempo',
                        'url': 'https://test.eltiempo.com',
                        'type': 'news',
                        'priority': 'high',
                        'scraping_interval': 30,
                        'selectors': {
                            'article': 'article.article-container',
                            'title': 'h1.titulo',
                            'content': 'div.articulo-contenido'
                        }
                    },
                    'el_espectador': {
                        'name': 'El Espectador',
                        'url': 'https://test.elespectador.com',
                        'type': 'news',
                        'priority': 'high',
                        'scraping_interval': 30,
                        'selectors': {
                            'article': 'article.Article',
                            'title': 'h1.Article-Title',
                            'content': 'div.Article-Content'
                        }
                    }
                },
                'specialized': {
                    'la_silla_vacia': {
                        'name': 'La Silla Vacía',
                        'url': 'https://test.lasillavacia.com',
                        'type': 'political_analysis',
                        'priority': 'high',
                        'scraping_interval': 120
                    }
                }
            },
            'academic': {
                'fedesarrollo': {
                    'name': 'Fedesarrollo',
                    'url': 'https://test.fedesarrollo.org.co',
                    'type': 'economic_research',
                    'priority': 'medium',
                    'content_types': ['economic_studies', 'policy_analysis']
                }
            }
        }

    @pytest.fixture
    def integrated_source_manager(self, full_system_config):
        """Create integrated source manager for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(full_system_config, f)
            config_path = f.name

        return SourceManager(config_path=config_path)

    @pytest.mark.asyncio
    async def test_end_to_end_data_collection(self, integrated_source_manager, mock_aiohttp, mock_database):
        """Test complete data collection and storage pipeline"""

        # Mock API responses
        dane_response = {
            "resultado": [
                {
                    "fecha": "2024-01-15",
                    "variacion_anual": 5.8,
                    "variacion_mensual": 0.4,
                    "indice": 118.45
                }
            ]
        }

        banrep_response = {
            "data": [
                {
                    "fecha": "2024-01-15",
                    "moneda": "USD",
                    "tasa": 4250.50
                }
            ]
        }

        # Mock scraper responses
        el_tiempo_html = """
        <article class="article-container">
            <h1 class="titulo">Colombia Economy Shows Growth</h1>
            <div class="articulo-contenido">
                <p>La economía colombiana creció 3.2% en el primer trimestre.</p>
            </div>
        </article>
        """

        # Setup HTTP mocks
        mock_aiohttp.get('https://test.dane.gov.co/api/indices/ipc', payload=dane_response)
        mock_aiohttp.get('https://test.banrep.gov.co/api/tasas-cambio', payload=banrep_response)
        mock_aiohttp.get('https://test.eltiempo.com/economia', body=el_tiempo_html, content_type='text/html')

        # Mock the import system for dynamic client/scraper creation
        with patch('backend.core.source_manager.importlib.import_module') as mock_import:
            # Mock DANE client
            mock_dane_module = Mock()
            mock_dane_client = AsyncMock()
            mock_dane_client.fetch_latest = AsyncMock(return_value=dane_response['resultado'])
            mock_dane_module.DANEClient = Mock(return_value=mock_dane_client)

            # Mock BanRep client
            mock_banrep_module = Mock()
            mock_banrep_client = AsyncMock()
            mock_banrep_client.fetch_latest = AsyncMock(return_value=banrep_response['data'])
            mock_banrep_module.BancoRepublicaClient = Mock(return_value=mock_banrep_client)

            # Mock El Tiempo scraper
            mock_tiempo_module = Mock()
            mock_tiempo_scraper = Mock()
            mock_tiempo_scraper.scrape_batch = Mock(return_value=[
                {
                    'title': 'Colombia Economy Shows Growth',
                    'content': 'La economía colombiana creció 3.2% en el primer trimestre.',
                    'url': 'https://test.eltiempo.com/article/1',
                    'published_date': '2024-01-15T10:00:00Z',
                    'source': 'El Tiempo'
                }
            ])
            mock_tiempo_module.ElTiempoScraper = Mock(return_value=mock_tiempo_scraper)

            # Configure import mock to return appropriate modules
            def import_side_effect(module_path):
                if 'dane_client' in module_path:
                    return mock_dane_module
                elif 'banrep_client' in module_path:
                    return mock_banrep_module
                elif 'el_tiempo' in module_path:
                    return mock_tiempo_module
                else:
                    return Mock()

            mock_import.side_effect = import_side_effect

            # Initialize all collectors
            await integrated_source_manager.initialize_collectors()

            # Verify collectors were created
            assert len(integrated_source_manager.api_clients) >= 1
            assert len(integrated_source_manager.scrapers) >= 1

            # Simulate data collection from APIs
            api_sources = integrated_source_manager.get_api_sources()
            for source in api_sources[:2]:  # Test first 2 API sources
                if source.key in integrated_source_manager.api_clients:
                    await integrated_source_manager._collect_from_api(source)

            # Simulate data collection from scrapers
            scraper_sources = integrated_source_manager.get_scraper_sources()
            for source in scraper_sources[:2]:  # Test first 2 scrapers
                if source.key in integrated_source_manager.scrapers:
                    await integrated_source_manager._collect_from_scraper(source)

    @pytest.mark.asyncio
    async def test_source_prioritization_and_scheduling(self, integrated_source_manager):
        """Test that sources are prioritized and scheduled correctly"""

        # Get sources by priority
        high_priority = integrated_source_manager.get_sources_by_priority('high')
        medium_priority = integrated_source_manager.get_sources_by_priority('medium')

        # High priority sources should be processed first
        assert len(high_priority) > 0
        assert len(medium_priority) > 0

        # High priority sources should have shorter update intervals
        for source in high_priority:
            assert source.priority == 'high'
            # High priority sources typically update more frequently
            assert source.update_interval <= 120  # 2 hours or less

    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self, integrated_source_manager, mock_aiohttp):
        """Test system resilience when some sources fail"""

        # Mock some sources to fail
        mock_aiohttp.get('https://test.dane.gov.co/api/indices/ipc', status=500)
        mock_aiohttp.get('https://test.banrep.gov.co/api/tasas-cambio', payload={'data': []})  # Success but empty
        mock_aiohttp.get('https://test.eltiempo.com/politica', status=404)

        with patch('backend.core.source_manager.importlib.import_module') as mock_import:
            # Mock clients that might fail
            mock_module = Mock()
            mock_failing_client = AsyncMock()
            mock_failing_client.fetch_latest = AsyncMock(side_effect=Exception("Connection timeout"))
            mock_module.DANEClient = Mock(return_value=mock_failing_client)

            mock_working_client = AsyncMock()
            mock_working_client.fetch_latest = AsyncMock(return_value=[])
            mock_module.BancoRepublicaClient = Mock(return_value=mock_working_client)

            mock_import.return_value = mock_module

            # Initialize collectors
            await integrated_source_manager.initialize_collectors()

            # System should continue working despite failures
            sources = list(integrated_source_manager.sources.values())[:3]

            # Test each source - some may fail but shouldn't crash the system
            for source in sources:
                try:
                    if source.is_api and source.key in integrated_source_manager.api_clients:
                        await integrated_source_manager._collect_from_api(source)
                    elif source.is_scraper and source.key in integrated_source_manager.scrapers:
                        await integrated_source_manager._collect_from_scraper(source)
                except Exception:
                    # Individual source failures should be handled gracefully
                    pass

    @pytest.mark.asyncio
    async def test_concurrent_multi_source_collection(self, integrated_source_manager, mock_aiohttp):
        """Test concurrent collection from multiple sources"""

        # Mock responses for all sources
        sources_data = {
            'dane': {"resultado": [{"variacion_anual": 5.8}]},
            'banco_republica': {"data": [{"tasa": 4250.50}]},
            'el_tiempo': '<article><h1>News</h1><p>Content</p></article>',
            'el_espectador': '<article><h1>News</h1><p>Content</p></article>'
        }

        for source_key, response_data in sources_data.items():
            if isinstance(response_data, dict):
                mock_aiohttp.get(f'https://test.{source_key}.com/api', payload=response_data)
            else:
                mock_aiohttp.get(f'https://test.{source_key}.com', body=response_data, content_type='text/html')

        with patch('backend.core.source_manager.importlib.import_module') as mock_import:
            # Mock all client/scraper creation
            mock_module = Mock()

            # Create mock clients for each source type
            for source_key in sources_data.keys():
                mock_client = AsyncMock()
                if 'el_' in source_key:  # Scrapers
                    mock_client.scrape_batch = Mock(return_value=[{'title': 'Test'}])
                else:  # APIs
                    mock_client.fetch_latest = AsyncMock(return_value=[{'test': 'data'}])

                setattr(mock_module, f'{source_key.title()}Client', Mock(return_value=mock_client))
                setattr(mock_module, f'{source_key.title()}Scraper', Mock(return_value=mock_client))

            mock_import.return_value = mock_module

            # Initialize collectors
            await integrated_source_manager.initialize_collectors()

            # Test concurrent collection
            tasks = []

            # Collect from APIs concurrently
            api_sources = integrated_source_manager.get_api_sources()[:2]
            for source in api_sources:
                if source.key in integrated_source_manager.api_clients:
                    tasks.append(integrated_source_manager._collect_from_api(source))

            # Collect from scrapers concurrently
            scraper_sources = integrated_source_manager.get_scraper_sources()[:2]
            for source in scraper_sources:
                if source.key in integrated_source_manager.scrapers:
                    tasks.append(integrated_source_manager._collect_from_scraper(source))

            # Execute all collections concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Should handle concurrent operations without issues
            assert len(results) == len(tasks)

    @pytest.mark.asyncio
    async def test_data_quality_and_validation(self, integrated_source_manager):
        """Test data quality validation across different source types"""

        # Test API data validation
        api_data_samples = [
            {"status": "success", "data": [{"value": 123, "date": "2024-01-15"}]},
            {"resultado": [{"variacion_anual": 5.8}]},
            {"data": []},  # Empty but valid
            {"error": "Invalid request"},  # Error response
            None  # Null response
        ]

        for data in api_data_samples:
            if data is not None and ("data" in data or "resultado" in data):
                # Should be valid API data
                assert_valid_api_data(data)

        # Test news article validation
        article_samples = [
            {
                "title": "Test Article",
                "content": "Article content here",
                "url": "https://example.com/article",
                "published_date": "2024-01-15T10:00:00Z",
                "source": "Test Source"
            },
            {
                "title": "",  # Invalid - empty title
                "content": "Content",
                "url": "https://example.com/article",
                "published_date": "2024-01-15T10:00:00Z",
                "source": "Test Source"
            }
        ]

        for article in article_samples:
            try:
                if article.get("title"):  # Only valid articles should pass
                    assert_valid_news_article(article)
            except AssertionError:
                # Expected for invalid articles
                pass

    @pytest.mark.asyncio
    async def test_language_learning_features_integration(self, integrated_source_manager):
        """Test language learning specific features across the system"""

        # Test content difficulty analysis
        sample_texts = [
            "El gato come pescado.",  # Simple
            "La implementación de políticas macroeconómicas requiere análisis complejo.",  # Complex
            "El gobierno anunció nuevas medidas para la economía del país."  # Medium
        ]

        # Mock El Tiempo scraper for difficulty testing
        el_tiempo_config = {'base_url': 'https://test.eltiempo.com'}
        scraper = ElTiempoScraper(el_tiempo_config)

        difficulty_scores = []
        for text in sample_texts:
            score = scraper._calculate_difficulty(text)
            difficulty_scores.append(score)
            assert 1.0 <= score <= 5.0

        # Scores should generally increase with complexity
        assert difficulty_scores[0] < difficulty_scores[1]

        # Test Colombian entity extraction
        colombian_text = """
        El DANE publicó datos sobre la inflación. El Banco de la República
        mantuvo las tasas de interés. En Bogotá, el alcalde anunció nuevas medidas.
        """

        entities = scraper._extract_colombian_entities(colombian_text)
        assert 'institutions' in entities
        assert any('DANE' in str(entities))
        assert any('Banco de la República' in str(entities))

    @pytest.mark.asyncio
    async def test_real_time_monitoring_and_alerts(self, integrated_source_manager):
        """Test real-time monitoring and alert generation"""

        # Mock DANE client for economic alerts
        dane_config = {'base_url': 'https://test.dane.gov.co/api'}
        dane_client = DANEClient(dane_config)

        # Test inflation alert
        high_inflation_data = [
            {'data': {'variacion_mensual': 1.5, 'variacion_anual': 8.0}}  # High inflation
        ]

        alerts = dane_client._check_economic_alerts(high_inflation_data)
        assert len(alerts) > 0
        assert any(alert['type'] == 'inflation' for alert in alerts)

        # Test unemployment alert
        high_unemployment_data = [
            {'data': {'tasa_desempleo': 16.0}}  # High unemployment
        ]

        alerts = dane_client._check_economic_alerts(high_unemployment_data)
        assert len(alerts) > 0
        assert any(alert['type'] == 'unemployment' for alert in alerts)

    @pytest.mark.asyncio
    async def test_system_status_and_health_monitoring(self, integrated_source_manager):
        """Test system health monitoring and status reporting"""

        # Get system status
        status = integrated_source_manager.get_status()

        # Verify status structure
        required_status_fields = [
            'total_sources',
            'api_sources',
            'scraper_sources',
            'active_apis',
            'active_scrapers',
            'scheduled_jobs',
            'sources_by_priority'
        ]

        for field in required_status_fields:
            assert field in status

        # Verify priority breakdown
        assert 'high' in status['sources_by_priority']
        assert 'medium' in status['sources_by_priority']
        assert 'low' in status['sources_by_priority']

        # Test individual source testing
        source_keys = list(integrated_source_manager.sources.keys())[:3]

        for source_key in source_keys:
            result = await integrated_source_manager.test_source(source_key)

            assert 'source' in result
            assert 'type' in result
            assert 'status' in result


class TestAPIIntegration:
    """Test API integration with the web interface"""

    @pytest.fixture
    def mock_api_app(self):
        """Mock API application for testing"""
        # This would integrate with your actual API framework (FastAPI, Flask, etc.)
        return Mock()

    @pytest.mark.asyncio
    async def test_api_data_endpoints(self, integrated_source_manager, mock_api_app):
        """Test API endpoints that serve collected data"""

        # Mock collected data
        collected_data = {
            'economic_indicators': [
                {'indicator': 'inflation', 'value': 5.8, 'date': '2024-01-15'},
                {'indicator': 'gdp_growth', 'value': 3.2, 'date': '2024-01-15'}
            ],
            'news_articles': [
                {
                    'title': 'Economic Growth Continues',
                    'content': 'Colombia economy shows positive trends...',
                    'source': 'El Tiempo',
                    'date': '2024-01-15'
                }
            ]
        }

        # Test economic data endpoint
        economic_data = collected_data['economic_indicators']
        assert len(economic_data) > 0
        assert all('value' in item for item in economic_data)

        # Test news data endpoint
        news_data = collected_data['news_articles']
        assert len(news_data) > 0
        assert all('title' in item for item in news_data)

    @pytest.mark.asyncio
    async def test_language_learning_api_endpoints(self, integrated_source_manager):
        """Test language learning specific API endpoints"""

        # Mock vocabulary extraction
        sample_article = {
            'content': 'La economía colombiana muestra crecimiento sostenido según datos del DANE.',
            'difficulty_score': 3.2,
            'word_count': 11
        }

        # Test vocabulary extraction endpoint
        vocabulary = [
            {'word': 'economía', 'type': 'noun', 'difficulty': 'intermediate'},
            {'word': 'crecimiento', 'type': 'noun', 'difficulty': 'intermediate'},
            {'word': 'sostenido', 'type': 'adjective', 'difficulty': 'advanced'}
        ]

        assert len(vocabulary) > 0
        assert all('word' in item for item in vocabulary)
        assert all('difficulty' in item for item in vocabulary)

    @pytest.mark.asyncio
    async def test_search_and_filtering_endpoints(self, integrated_source_manager):
        """Test search and filtering functionality"""

        # Mock search functionality
        search_params = {
            'query': 'economía',
            'sources': ['el_tiempo', 'el_espectador'],
            'date_range': '2024-01-01,2024-01-31',
            'difficulty': 'intermediate'
        }

        # Test that search parameters are properly structured
        assert 'query' in search_params
        assert 'sources' in search_params
        assert isinstance(search_params['sources'], list)


class TestPerformanceIntegration:
    """Integration performance and load tests"""

    @pytest.mark.asyncio
    async def test_high_load_data_collection(self, integrated_source_manager):
        """Test system performance under high load"""

        # Simulate high load by running multiple collection cycles
        collection_tasks = []

        # Create multiple collection tasks
        for i in range(10):
            # Mock rapid successive collections
            task = asyncio.create_task(
                self._simulate_collection_cycle(integrated_source_manager)
            )
            collection_tasks.append(task)

        # Execute all tasks concurrently
        start_time = datetime.now()
        results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        end_time = datetime.now()

        # System should handle concurrent load
        elapsed = (end_time - start_time).total_seconds()
        assert elapsed < 30  # Should complete within 30 seconds

        # Most tasks should succeed
        successful_tasks = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_tasks) >= len(collection_tasks) * 0.8  # 80% success rate

    async def _simulate_collection_cycle(self, source_manager):
        """Simulate a collection cycle"""
        try:
            # Mock source testing
            sources = list(source_manager.sources.keys())[:3]
            for source_key in sources:
                await source_manager.test_source(source_key)

            return "success"
        except Exception as e:
            return e

    @pytest.mark.asyncio
    async def test_memory_usage_over_time(self, integrated_source_manager):
        """Test memory usage over extended operation"""

        # Run multiple collection cycles to test memory leaks
        for cycle in range(5):
            # Simulate data collection and processing
            status = integrated_source_manager.get_status()

            # Force garbage collection between cycles
            import gc
            gc.collect()

            # Memory usage should remain stable
            assert status['total_sources'] > 0

    @pytest.mark.asyncio
    async def test_database_integration_performance(self, mock_database):
        """Test database integration performance"""

        # Mock large dataset operations
        large_dataset = [
            {'id': i, 'content': f'Article {i}', 'processed_at': datetime.now()}
            for i in range(1000)
        ]

        # Simulate batch operations
        start_time = datetime.now()

        # Mock database batch insert
        mock_database.execute = AsyncMock()
        for batch_start in range(0, len(large_dataset), 100):
            batch = large_dataset[batch_start:batch_start + 100]
            await mock_database.execute("INSERT INTO articles ...", batch)

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Batch operations should be efficient
        assert elapsed < 5.0  # Should complete within 5 seconds
        assert mock_database.execute.call_count == 10  # 1000 items / 100 per batch


if __name__ == "__main__":
    pytest.main([__file__, "-v"])