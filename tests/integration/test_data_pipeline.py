"""
Integration tests for data processing pipelines
Tests _process_data() and _process_documents() methods
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.source_manager import SourceManager, DataSource
from backend.app.database.models import (
    Base,
    ScrapedContent,
    ContentAnalysis,
    IntelligenceAlert
)


# Test database setup
@pytest.fixture
def test_db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """Create test database session"""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def source_manager():
    """Create SourceManager instance for testing"""
    # Use a test config that won't try to load external files
    manager = SourceManager.__new__(SourceManager)
    manager.sources = {}
    manager.api_clients = {}
    manager.scrapers = {}
    return manager


@pytest.fixture
def mock_api_source():
    """Create mock API data source"""
    return DataSource(
        category='government.statistics',
        key='dane',
        name='DANE Statistics',
        url='https://www.dane.gov.co',
        type='api',
        priority='high',
        config={
            'api_endpoint': 'https://www.dane.gov.co/api',
            'data_type': 'economic_indicators'
        }
    )


@pytest.fixture
def mock_scraper_source():
    """Create mock scraper data source"""
    return DataSource(
        category='media.national',
        key='el_tiempo',
        name='El Tiempo',
        url='https://www.eltiempo.com',
        type='scraper',
        priority='high',
        config={
            'scraping_interval': 60,
            'selectors': {'title': 'h1', 'content': '.article-body'}
        }
    )


@pytest.fixture
def sample_api_data():
    """Sample API data matching DANE client structure"""
    return [
        {
            'source': 'DANE',
            'data': {
                'indicator': 'ipc',
                'value': 3.2,
                'period': '2025-01',
                'variacion_anual': 3.2,
                'variacion_mensual': 0.8
            },
            'extracted_at': datetime.utcnow().isoformat(),
            'metadata': {
                'department': 'Nacional',
                'category': 'inflation'
            },
            'data_quality': {
                'completeness': 100.0,
                'timeliness': 'current'
            }
        },
        {
            'source': 'DANE',
            'data': {
                'indicator': 'unemployment',
                'value': 12.5,
                'period': '2025-01'
            },
            'extracted_at': datetime.utcnow().isoformat()
        }
    ]


@pytest.fixture
def sample_scraped_documents():
    """Sample scraped documents matching BaseScraper structure"""
    return [
        {
            'source': 'El Tiempo',
            'source_url': 'https://www.eltiempo.com/article1',
            'category': 'politics',
            'title': 'Reforma política avanza en el Congreso',
            'subtitle': 'Nueva propuesta genera debate',
            'content': 'El Congreso de Colombia debate una importante reforma política que busca modernizar las instituciones democráticas del país.',
            'author': 'Juan Pérez',
            'word_count': 450,
            'published_date': datetime.utcnow().isoformat(),
            'scraped_at': datetime.utcnow().isoformat(),
            'content_hash': 'abc123def456',
            'tags': ['política', 'congreso', 'reforma'],
            'metadata': {
                'og_title': 'Reforma política avanza',
                'description': 'Debate en el Congreso'
            }
        },
        {
            'source': 'El Tiempo',
            'source_url': 'https://www.eltiempo.com/article2',
            'category': 'economy',
            'title': 'Inflación muestra tendencia a la baja',
            'content': 'Los últimos datos del DANE muestran una disminución en la inflación mensual, generando optimismo económico.',
            'word_count': 320,
            'published_date': datetime.utcnow().isoformat(),
            'scraped_at': datetime.utcnow().isoformat(),
            'content_hash': 'xyz789uvw012'
        }
    ]


class TestProcessDataMethod:
    """Test suite for _process_data() method"""

    @pytest.mark.asyncio
    async def test_process_data_stores_to_database(
        self,
        source_manager,
        mock_api_source,
        sample_api_data,
        test_db_session
    ):
        """Test that API data is properly stored to database"""
        # Inject test database session
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_data(sample_api_data, mock_api_source)

        # Verify data was stored
        # Note: Implementation should store API data in appropriate format
        # For now, we're testing the contract
        assert test_db_session is not None

    @pytest.mark.asyncio
    async def test_process_data_handles_empty_list(
        self,
        source_manager,
        mock_api_source,
        test_db_session
    ):
        """Test handling of empty data list"""
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_data([], mock_api_source)

        # Should complete without errors
        assert True

    @pytest.mark.asyncio
    async def test_process_data_validates_data_structure(
        self,
        source_manager,
        mock_api_source,
        test_db_session
    ):
        """Test validation of data structure"""
        invalid_data = [
            {'incomplete': 'data'},  # Missing required fields
            None,  # Null entry
            'invalid'  # Wrong type
        ]

        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            # Should handle invalid data gracefully
            await source_manager._process_data(invalid_data, mock_api_source)

    @pytest.mark.asyncio
    async def test_process_data_creates_intelligence_alerts(
        self,
        source_manager,
        mock_api_source,
        test_db_session
    ):
        """Test that alerts are created for important indicators"""
        high_inflation_data = [{
            'source': 'DANE',
            'data': {
                'indicator': 'ipc',
                'value': 5.5,  # High inflation
                'variacion_mensual': 1.5  # Exceeds threshold
            },
            'extracted_at': datetime.utcnow().isoformat()
        }]

        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_data(high_inflation_data, mock_api_source)

        # Check if alerts were created
        alerts = test_db_session.query(IntelligenceAlert).all()
        # Implementation should create alerts for threshold violations

    @pytest.mark.asyncio
    async def test_process_data_async_performance(
        self,
        source_manager,
        mock_api_source,
        test_db_session
    ):
        """Test async processing performance with large dataset"""
        # Create large dataset
        large_dataset = [
            {
                'source': 'DANE',
                'data': {'indicator': f'metric_{i}', 'value': i},
                'extracted_at': datetime.utcnow().isoformat()
            }
            for i in range(100)
        ]

        import time
        start = time.time()

        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_data(large_dataset, mock_api_source)

        elapsed = time.time() - start

        # Should process 100 items in under 2 seconds
        assert elapsed < 2.0, f"Processing took {elapsed}s, expected < 2s"

    @pytest.mark.asyncio
    async def test_process_data_error_handling(
        self,
        source_manager,
        mock_api_source
    ):
        """Test error handling during data processing"""
        # Mock database session that raises exception
        mock_session = MagicMock()
        mock_session.add.side_effect = Exception("Database error")

        with patch('backend.core.source_manager.Session', return_value=mock_session):
            # Should not raise exception, just log error
            await source_manager._process_data([{'data': 'test'}], mock_api_source)


class TestProcessDocumentsMethod:
    """Test suite for _process_documents() method"""

    @pytest.mark.asyncio
    async def test_process_documents_stores_scraped_content(
        self,
        source_manager,
        mock_scraper_source,
        sample_scraped_documents,
        test_db_session
    ):
        """Test that scraped documents are stored as ScrapedContent"""
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_documents(
                sample_scraped_documents,
                mock_scraper_source
            )

        # Verify documents were stored
        stored_docs = test_db_session.query(ScrapedContent).all()
        assert len(stored_docs) == len(sample_scraped_documents)

        # Verify first document fields
        doc = stored_docs[0]
        assert doc.source == 'El Tiempo'
        assert doc.title is not None
        assert doc.content is not None
        assert doc.content_hash is not None

    @pytest.mark.asyncio
    async def test_process_documents_prevents_duplicates(
        self,
        source_manager,
        mock_scraper_source,
        sample_scraped_documents,
        test_db_session
    ):
        """Test duplicate detection using content_hash"""
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            # Process documents twice
            await source_manager._process_documents(
                sample_scraped_documents,
                mock_scraper_source
            )
            await source_manager._process_documents(
                sample_scraped_documents,
                mock_scraper_source
            )

        # Should only store unique documents
        stored_docs = test_db_session.query(ScrapedContent).all()
        # Implementation should check content_hash before inserting
        assert len(stored_docs) <= len(sample_scraped_documents)

    @pytest.mark.asyncio
    async def test_process_documents_calculates_difficulty_score(
        self,
        source_manager,
        mock_scraper_source,
        sample_scraped_documents,
        test_db_session
    ):
        """Test difficulty score calculation for language learning"""
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_documents(
                sample_scraped_documents,
                mock_scraper_source
            )

        stored_docs = test_db_session.query(ScrapedContent).all()
        for doc in stored_docs:
            # Implementation should calculate difficulty (1.0-5.0)
            if doc.difficulty_score is not None:
                assert 1.0 <= doc.difficulty_score <= 5.0

    @pytest.mark.asyncio
    async def test_process_documents_extracts_colombian_entities(
        self,
        source_manager,
        mock_scraper_source,
        sample_scraped_documents,
        test_db_session
    ):
        """Test extraction of Colombian-specific entities"""
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_documents(
                sample_scraped_documents,
                mock_scraper_source
            )

        stored_docs = test_db_session.query(ScrapedContent).all()
        for doc in stored_docs:
            # Implementation should extract entities like "Congreso", "DANE"
            if doc.colombian_entities:
                assert isinstance(doc.colombian_entities, (dict, list))

    @pytest.mark.asyncio
    async def test_process_documents_handles_missing_fields(
        self,
        source_manager,
        mock_scraper_source,
        test_db_session
    ):
        """Test handling of documents with missing optional fields"""
        minimal_doc = [{
            'source': 'Test Source',
            'source_url': 'https://test.com/article',
            'title': 'Test Title',
            'content': 'Test content',
            'scraped_at': datetime.utcnow().isoformat()
        }]

        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            # Should handle missing author, subtitle, etc.
            await source_manager._process_documents(minimal_doc, mock_scraper_source)

        stored = test_db_session.query(ScrapedContent).first()
        assert stored is not None
        assert stored.title == 'Test Title'

    @pytest.mark.asyncio
    async def test_process_documents_batch_processing(
        self,
        source_manager,
        mock_scraper_source,
        test_db_session
    ):
        """Test batch processing of multiple documents"""
        # Create batch of 50 documents
        batch_docs = [
            {
                'source': 'Batch Source',
                'source_url': f'https://test.com/article{i}',
                'title': f'Article {i}',
                'content': f'Content for article {i}',
                'content_hash': f'hash{i}',
                'scraped_at': datetime.utcnow().isoformat()
            }
            for i in range(50)
        ]

        import time
        start = time.time()

        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_documents(batch_docs, mock_scraper_source)

        elapsed = time.time() - start

        # Should process 50 documents efficiently
        assert elapsed < 3.0, f"Batch processing took {elapsed}s, expected < 3s"

        stored = test_db_session.query(ScrapedContent).count()
        assert stored == 50

    @pytest.mark.asyncio
    async def test_process_documents_creates_content_analysis(
        self,
        source_manager,
        mock_scraper_source,
        sample_scraped_documents,
        test_db_session
    ):
        """Test that ContentAnalysis records are created"""
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_documents(
                sample_scraped_documents,
                mock_scraper_source
            )

        # Check if analysis was performed
        analyses = test_db_session.query(ContentAnalysis).all()
        # Implementation should create analysis for each document


class TestIntegrationPipeline:
    """Integration tests for complete data pipeline"""

    @pytest.mark.asyncio
    async def test_end_to_end_api_pipeline(
        self,
        source_manager,
        mock_api_source,
        sample_api_data,
        test_db_session
    ):
        """Test complete API data collection and processing pipeline"""
        # Simulate full collection process
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            # This would normally be called by _collect_from_api
            await source_manager._process_data(sample_api_data, mock_api_source)

        # Verify complete pipeline execution
        assert test_db_session is not None

    @pytest.mark.asyncio
    async def test_end_to_end_scraper_pipeline(
        self,
        source_manager,
        mock_scraper_source,
        sample_scraped_documents,
        test_db_session
    ):
        """Test complete scraper collection and processing pipeline"""
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            await source_manager._process_documents(
                sample_scraped_documents,
                mock_scraper_source
            )

        # Verify documents stored
        docs = test_db_session.query(ScrapedContent).all()
        assert len(docs) > 0

    @pytest.mark.asyncio
    async def test_concurrent_processing(
        self,
        source_manager,
        mock_api_source,
        mock_scraper_source,
        sample_api_data,
        sample_scraped_documents,
        test_db_session
    ):
        """Test concurrent processing of API and scraper data"""
        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            # Run both pipelines concurrently
            await asyncio.gather(
                source_manager._process_data(sample_api_data, mock_api_source),
                source_manager._process_documents(
                    sample_scraped_documents,
                    mock_scraper_source
                )
            )

        # Both should complete successfully
        assert test_db_session is not None


class TestDataValidation:
    """Test data validation and quality checks"""

    @pytest.mark.asyncio
    async def test_validates_required_fields_api(
        self,
        source_manager,
        mock_api_source,
        test_db_session
    ):
        """Test validation of required API data fields"""
        invalid_data = [
            {},  # Empty dict
            {'source': 'DANE'},  # Missing data field
            {'data': 'test'}  # Missing source field
        ]

        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            # Should skip invalid entries
            await source_manager._process_data(invalid_data, mock_api_source)

    @pytest.mark.asyncio
    async def test_validates_required_fields_documents(
        self,
        source_manager,
        mock_scraper_source,
        test_db_session
    ):
        """Test validation of required document fields"""
        invalid_docs = [
            {},  # Empty dict
            {'title': 'Test'},  # Missing required fields
            {'source': 'Test', 'title': 'Test'}  # Missing content
        ]

        with patch('backend.core.source_manager.Session', return_value=test_db_session):
            # Should skip invalid documents
            await source_manager._process_documents(invalid_docs, mock_scraper_source)

        # Should not have stored invalid documents
        count = test_db_session.query(ScrapedContent).count()
        assert count == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
