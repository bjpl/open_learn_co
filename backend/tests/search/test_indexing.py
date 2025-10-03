"""
Tests for Indexing Service

Tests index operations, bulk indexing, and document management
"""

import pytest
from datetime import datetime

from app.services.indexer_service import IndexerService, get_indexer_service
from app.search.elasticsearch_client import get_elasticsearch_client


@pytest.fixture
async def indexer_service():
    """Indexer service fixture"""
    return get_indexer_service()


@pytest.fixture
async def clean_indices():
    """Clean up indices before and after tests"""
    client = await get_elasticsearch_client()

    # Cleanup before
    for index in ["articles", "vocabulary", "analysis"]:
        try:
            await client.delete_index(index)
        except:
            pass

    yield

    # Cleanup after
    for index in ["articles", "vocabulary", "analysis"]:
        try:
            await client.delete_index(index)
        except:
            pass


class TestIndexerService:
    """Test indexer service operations"""

    @pytest.mark.asyncio
    async def test_initialize_indices(self, indexer_service, clean_indices):
        """Test index initialization"""
        results = await indexer_service.initialize_indices(recreate=False)

        assert "articles" in results
        assert "vocabulary" in results
        assert "analysis" in results

        # Verify all created successfully
        for index_name, created in results.items():
            assert created is True

    @pytest.mark.asyncio
    async def test_initialize_indices_recreate(self, indexer_service, clean_indices):
        """Test index recreation"""
        # Create indices
        await indexer_service.initialize_indices(recreate=False)

        # Recreate
        results = await indexer_service.initialize_indices(recreate=True)

        # Should successfully recreate
        for index_name, created in results.items():
            assert created is True

    @pytest.mark.asyncio
    async def test_index_article(self, indexer_service, clean_indices):
        """Test indexing single article"""
        # Initialize indices
        await indexer_service.initialize_indices()

        # Index article
        article = {
            "id": "test-1",
            "title": "Test Article",
            "content": "This is test content",
            "summary": "Test summary",
            "source": "Test Source",
            "category": "test",
            "url": "https://test.com/article"
        }

        success = await indexer_service.index_article(article)
        assert success is True

    @pytest.mark.asyncio
    async def test_index_articles_bulk(self, indexer_service, clean_indices):
        """Test bulk article indexing"""
        # Initialize indices
        await indexer_service.initialize_indices()

        # Prepare articles
        articles = [
            {
                "id": f"test-{i}",
                "title": f"Test Article {i}",
                "content": f"Content {i}",
                "summary": f"Summary {i}",
                "source": "Test",
                "category": "test",
                "url": f"https://test.com/{i}"
            }
            for i in range(10)
        ]

        # Bulk index
        result = await indexer_service.index_articles_bulk(articles, refresh=True)

        assert result["success"] == 10
        assert len(result.get("errors", [])) == 0

    @pytest.mark.asyncio
    async def test_index_vocabulary(self, indexer_service, clean_indices):
        """Test indexing vocabulary"""
        # Initialize indices
        await indexer_service.initialize_indices()

        # Index vocabulary
        vocab = {
            "id": "vocab-1",
            "lemma": "test",
            "definition": "A test word",
            "difficulty_level": "A1",
            "part_of_speech": "noun"
        }

        success = await indexer_service.index_vocabulary(vocab)
        assert success is True

    @pytest.mark.asyncio
    async def test_index_vocabulary_bulk(self, indexer_service, clean_indices):
        """Test bulk vocabulary indexing"""
        # Initialize indices
        await indexer_service.initialize_indices()

        # Prepare vocabulary
        vocabulary = [
            {
                "id": f"vocab-{i}",
                "lemma": f"word{i}",
                "definition": f"Definition {i}",
                "difficulty_level": "A1",
                "part_of_speech": "noun"
            }
            for i in range(5)
        ]

        # Bulk index
        result = await indexer_service.index_vocabulary_bulk(vocabulary, refresh=True)

        assert result["success"] == 5
        assert len(result.get("errors", [])) == 0

    @pytest.mark.asyncio
    async def test_update_article(self, indexer_service, clean_indices):
        """Test updating article"""
        # Initialize and index
        await indexer_service.initialize_indices()

        article = {
            "id": "update-test",
            "title": "Original Title",
            "content": "Original content",
            "source": "Test",
            "category": "test",
            "url": "https://test.com"
        }

        await indexer_service.index_article(article)

        # Update
        success = await indexer_service.update_article(
            article_id="update-test",
            updates={"title": "Updated Title"}
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_delete_article(self, indexer_service, clean_indices):
        """Test deleting article"""
        # Initialize and index
        await indexer_service.initialize_indices()

        article = {
            "id": "delete-test",
            "title": "To Delete",
            "content": "Content",
            "source": "Test",
            "category": "test",
            "url": "https://test.com"
        }

        await indexer_service.index_article(article)

        # Delete
        success = await indexer_service.delete_article("delete-test")
        assert success is True

    @pytest.mark.asyncio
    async def test_index_analysis(self, indexer_service, clean_indices):
        """Test indexing analysis results"""
        # Initialize indices
        await indexer_service.initialize_indices()

        # Index analysis
        analysis = {
            "id": "analysis-1",
            "content_id": "article-1",
            "content_type": "article",
            "analysis_type": "sentiment",
            "results": {
                "sentiment": "positive",
                "score": 0.85
            },
            "confidence_score": 0.92
        }

        success = await indexer_service.index_analysis(analysis)
        assert success is True


class TestDocumentPreparation:
    """Test document preparation methods"""

    @pytest.mark.asyncio
    async def test_prepare_article_document(self, indexer_service):
        """Test article document preparation"""
        article = {
            "id": "1",
            "title": "Test",
            "content": "Content",
            "source": "Source",
            "category": "Category",
            "url": "https://test.com",
            "sentiment_score": 0.5,
            "entities": [{"name": "Test", "type": "ORG"}]
        }

        doc = indexer_service._prepare_article_document(article)

        assert doc["id"] == "1"
        assert doc["title"] == "Test"
        assert doc["content"] == "Content"
        assert "indexed_at" in doc
        assert doc["sentiment_score"] == 0.5
        assert doc["entities"] == article["entities"]

    @pytest.mark.asyncio
    async def test_prepare_vocabulary_document(self, indexer_service):
        """Test vocabulary document preparation"""
        vocab = {
            "id": "v1",
            "lemma": "test",
            "definition": "A test",
            "difficulty_level": "A1",
            "part_of_speech": "noun",
            "translations": "test",
            "frequency_rank": 100
        }

        doc = indexer_service._prepare_vocabulary_document(vocab)

        assert doc["id"] == "v1"
        assert doc["lemma"] == "test"
        assert doc["definition"] == "A test"
        assert "created_at" in doc
        assert doc["frequency_rank"] == 100

    @pytest.mark.asyncio
    async def test_prepare_analysis_document(self, indexer_service):
        """Test analysis document preparation"""
        analysis = {
            "id": "a1",
            "content_id": "article-1",
            "analysis_type": "sentiment",
            "results": {"score": 0.8},
            "confidence_score": 0.9
        }

        doc = indexer_service._prepare_analysis_document(analysis)

        assert doc["id"] == "a1"
        assert doc["content_id"] == "article-1"
        assert doc["analysis_type"] == "sentiment"
        assert "created_at" in doc


class TestServiceSingleton:
    """Test service singleton"""

    def test_get_indexer_service(self):
        """Test getting indexer service singleton"""
        service1 = get_indexer_service()
        service2 = get_indexer_service()

        assert service1 is service2
