"""
Tests for Search Service

Tests search functionality, facets, and autocomplete
"""

import pytest
from datetime import datetime, timedelta

from app.services.search_service import SearchService, get_search_service
from app.services.indexer_service import get_indexer_service
from app.search.elasticsearch_client import get_elasticsearch_client


@pytest.fixture
async def search_service():
    """Search service fixture"""
    return get_search_service()


@pytest.fixture
async def indexer_service():
    """Indexer service fixture"""
    return get_indexer_service()


@pytest.fixture
async def setup_test_data(indexer_service):
    """Setup test data in Elasticsearch"""
    # Initialize indices
    await indexer_service.initialize_indices(recreate=True)

    # Index test articles
    test_articles = [
        {
            "id": "1",
            "title": "Colombian Coffee Production Increases",
            "content": "Colombian coffee production has increased this year",
            "summary": "Coffee production up in Colombia",
            "source": "El Tiempo",
            "category": "economy",
            "sentiment_label": "positive",
            "difficulty_level": "B1",
            "published_date": datetime.utcnow().isoformat()
        },
        {
            "id": "2",
            "title": "Political News from Bogota",
            "content": "Political developments in Bogota this week",
            "summary": "Politics in the capital",
            "source": "Semana",
            "category": "politics",
            "sentiment_label": "neutral",
            "difficulty_level": "C1",
            "published_date": (datetime.utcnow() - timedelta(days=1)).isoformat()
        },
        {
            "id": "3",
            "title": "Colombian Football Victory",
            "content": "The national team won the match",
            "summary": "Sports victory",
            "source": "El Tiempo",
            "category": "sports",
            "sentiment_label": "positive",
            "difficulty_level": "A2",
            "published_date": (datetime.utcnow() - timedelta(days=2)).isoformat()
        }
    ]

    await indexer_service.index_articles_bulk(test_articles, refresh=True)

    # Index test vocabulary
    test_vocab = [
        {
            "id": "v1",
            "lemma": "café",
            "definition": "Bebida hecha de granos de café",
            "translations": "coffee",
            "difficulty_level": "A1",
            "part_of_speech": "noun",
            "regional_variant": "Colombia"
        },
        {
            "id": "v2",
            "lemma": "fútbol",
            "definition": "Deporte de equipo",
            "translations": "football, soccer",
            "difficulty_level": "A1",
            "part_of_speech": "noun",
            "regional_variant": "Colombia"
        }
    ]

    await indexer_service.index_vocabulary_bulk(test_vocab, refresh=True)

    yield

    # Cleanup
    client = await get_elasticsearch_client()
    await client.delete_index("articles")
    await client.delete_index("vocabulary")


class TestSearchService:
    """Test search service operations"""

    @pytest.mark.asyncio
    async def test_search_articles_basic(self, search_service, setup_test_data):
        """Test basic article search"""
        results = await search_service.search_articles(
            query="coffee",
            page=1,
            page_size=10
        )

        assert results["total"] > 0
        assert len(results["hits"]) > 0
        assert "coffee" in results["hits"][0]["title"].lower()

    @pytest.mark.asyncio
    async def test_search_articles_with_filters(self, search_service, setup_test_data):
        """Test article search with filters"""
        # Filter by source
        results = await search_service.search_articles(
            query="",
            filters={"source": "El Tiempo"},
            page=1,
            page_size=10
        )

        assert results["total"] > 0
        for hit in results["hits"]:
            assert hit["source"] == "El Tiempo"

        # Filter by category
        results = await search_service.search_articles(
            query="",
            filters={"category": "politics"},
            page=1,
            page_size=10
        )

        assert results["total"] > 0
        for hit in results["hits"]:
            assert hit["category"] == "politics"

    @pytest.mark.asyncio
    async def test_search_articles_pagination(self, search_service, setup_test_data):
        """Test article search pagination"""
        # First page
        page1 = await search_service.search_articles(
            query="",
            page=1,
            page_size=2
        )

        assert len(page1["hits"]) <= 2
        assert page1["page"] == 1

        # Second page
        page2 = await search_service.search_articles(
            query="",
            page=2,
            page_size=2
        )

        assert page2["page"] == 2

    @pytest.mark.asyncio
    async def test_search_articles_sorting(self, search_service, setup_test_data):
        """Test article search sorting"""
        # Sort by published date
        results = await search_service.search_articles(
            query="",
            sort_by="published_date",
            page=1,
            page_size=10
        )

        assert results["total"] > 0

        # Verify descending order
        dates = [hit.get("published_date") for hit in results["hits"] if "published_date" in hit]
        if len(dates) > 1:
            assert dates[0] >= dates[1]

    @pytest.mark.asyncio
    async def test_autocomplete(self, search_service, setup_test_data):
        """Test autocomplete suggestions"""
        suggestions = await search_service.autocomplete(
            query="coff",
            field="title",
            size=5
        )

        assert len(suggestions) > 0
        assert any("coffee" in s.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_search_vocabulary(self, search_service, setup_test_data):
        """Test vocabulary search"""
        results = await search_service.search_vocabulary(
            query="café",
            page=1,
            page_size=10
        )

        assert results["total"] > 0
        assert len(results["hits"]) > 0
        assert "café" in results["hits"][0]["lemma"].lower()

    @pytest.mark.asyncio
    async def test_search_vocabulary_with_filters(self, search_service, setup_test_data):
        """Test vocabulary search with filters"""
        results = await search_service.search_vocabulary(
            query="",
            filters={"difficulty_level": "A1"},
            page=1,
            page_size=10
        )

        assert results["total"] > 0
        for hit in results["hits"]:
            assert hit["difficulty_level"] == "A1"

    @pytest.mark.asyncio
    async def test_get_facets_articles(self, search_service, setup_test_data):
        """Test getting article facets"""
        facets = await search_service.get_facets(index="articles")

        assert "sources" in facets
        assert "categories" in facets
        assert "sentiment" in facets

        # Verify facet structure
        if facets["sources"]:
            assert "value" in facets["sources"][0]
            assert "count" in facets["sources"][0]

    @pytest.mark.asyncio
    async def test_get_facets_vocabulary(self, search_service, setup_test_data):
        """Test getting vocabulary facets"""
        facets = await search_service.get_facets(index="vocabulary")

        assert "difficulty" in facets
        assert "part_of_speech" in facets


class TestServiceSingleton:
    """Test service singleton pattern"""

    def test_get_search_service(self):
        """Test getting service singleton"""
        service1 = get_search_service()
        service2 = get_search_service()

        assert service1 is service2
