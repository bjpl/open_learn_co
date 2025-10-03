"""
Tests for Elasticsearch Client

Tests connection management, index operations, and bulk indexing
"""

import pytest
from typing import Dict, Any

from app.search.elasticsearch_client import ElasticsearchClient, get_elasticsearch_client


@pytest.fixture
async def es_client():
    """Elasticsearch client fixture"""
    client = ElasticsearchClient()
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
def test_index_name():
    """Test index name"""
    return "test_articles"


@pytest.fixture
def test_mappings():
    """Test index mappings"""
    return {
        "properties": {
            "title": {"type": "text"},
            "content": {"type": "text"},
            "category": {"type": "keyword"}
        }
    }


class TestElasticsearchClient:
    """Test Elasticsearch client operations"""

    @pytest.mark.asyncio
    async def test_connection(self, es_client):
        """Test successful connection"""
        assert es_client.is_connected is True

    @pytest.mark.asyncio
    async def test_health_check(self, es_client):
        """Test health check"""
        health = await es_client.health_check()

        assert "status" in health
        assert "healthy" in health
        assert health["healthy"] is True

    @pytest.mark.asyncio
    async def test_create_index(self, es_client, test_index_name, test_mappings):
        """Test index creation"""
        try:
            # Create index
            created = await es_client.create_index(
                index_name=test_index_name,
                mappings=test_mappings
            )
            assert created is True

            # Verify index exists
            exists = await es_client.index_exists(test_index_name)
            assert exists is True

        finally:
            # Cleanup
            await es_client.delete_index(test_index_name)

    @pytest.mark.asyncio
    async def test_delete_index(self, es_client, test_index_name, test_mappings):
        """Test index deletion"""
        # Create index
        await es_client.create_index(
            index_name=test_index_name,
            mappings=test_mappings
        )

        # Delete index
        deleted = await es_client.delete_index(test_index_name)
        assert deleted is True

        # Verify index doesn't exist
        exists = await es_client.index_exists(test_index_name)
        assert exists is False

    @pytest.mark.asyncio
    async def test_bulk_index(self, es_client, test_index_name, test_mappings):
        """Test bulk indexing"""
        try:
            # Create index
            await es_client.create_index(
                index_name=test_index_name,
                mappings=test_mappings
            )

            # Prepare documents
            documents = [
                {
                    "id": "1",
                    "title": "Test Article 1",
                    "content": "This is test content",
                    "category": "test"
                },
                {
                    "id": "2",
                    "title": "Test Article 2",
                    "content": "More test content",
                    "category": "test"
                }
            ]

            # Bulk index
            result = await es_client.bulk_index(
                index_name=test_index_name,
                documents=documents,
                id_field="id"
            )

            assert result["success"] == 2
            assert len(result.get("errors", [])) == 0

            # Refresh index
            await es_client.refresh_index(test_index_name)

        finally:
            # Cleanup
            await es_client.delete_index(test_index_name)

    @pytest.mark.asyncio
    async def test_search(self, es_client, test_index_name, test_mappings):
        """Test search operation"""
        try:
            # Create index
            await es_client.create_index(
                index_name=test_index_name,
                mappings=test_mappings
            )

            # Index documents
            documents = [
                {
                    "id": "1",
                    "title": "Colombian Coffee",
                    "content": "Colombian coffee is the best",
                    "category": "food"
                }
            ]

            await es_client.bulk_index(
                index_name=test_index_name,
                documents=documents,
                id_field="id"
            )

            await es_client.refresh_index(test_index_name)

            # Search
            query = {
                "match": {
                    "title": "coffee"
                }
            }

            results = await es_client.search(
                index_name=test_index_name,
                query=query
            )

            assert results["hits"]["total"]["value"] > 0
            assert "coffee" in results["hits"]["hits"][0]["_source"]["title"].lower()

        finally:
            # Cleanup
            await es_client.delete_index(test_index_name)

    @pytest.mark.asyncio
    async def test_update_document(self, es_client, test_index_name, test_mappings):
        """Test document update"""
        try:
            # Create index and document
            await es_client.create_index(
                index_name=test_index_name,
                mappings=test_mappings
            )

            documents = [
                {
                    "id": "1",
                    "title": "Original Title",
                    "content": "Original content",
                    "category": "test"
                }
            ]

            await es_client.bulk_index(
                index_name=test_index_name,
                documents=documents,
                id_field="id"
            )

            await es_client.refresh_index(test_index_name)

            # Update document
            await es_client.update_document(
                index_name=test_index_name,
                doc_id="1",
                document={"title": "Updated Title"}
            )

            await es_client.refresh_index(test_index_name)

            # Verify update
            results = await es_client.search(
                index_name=test_index_name,
                query={"match_all": {}}
            )

            assert results["hits"]["hits"][0]["_source"]["title"] == "Updated Title"

        finally:
            # Cleanup
            await es_client.delete_index(test_index_name)

    @pytest.mark.asyncio
    async def test_delete_document(self, es_client, test_index_name, test_mappings):
        """Test document deletion"""
        try:
            # Create index and document
            await es_client.create_index(
                index_name=test_index_name,
                mappings=test_mappings
            )

            documents = [
                {"id": "1", "title": "Test", "content": "Test", "category": "test"}
            ]

            await es_client.bulk_index(
                index_name=test_index_name,
                documents=documents,
                id_field="id"
            )

            await es_client.refresh_index(test_index_name)

            # Delete document
            await es_client.delete_document(
                index_name=test_index_name,
                doc_id="1"
            )

            await es_client.refresh_index(test_index_name)

            # Verify deletion
            results = await es_client.search(
                index_name=test_index_name,
                query={"match_all": {}}
            )

            assert results["hits"]["total"]["value"] == 0

        finally:
            # Cleanup
            await es_client.delete_index(test_index_name)


class TestClientSingleton:
    """Test client singleton pattern"""

    @pytest.mark.asyncio
    async def test_get_elasticsearch_client(self):
        """Test getting client singleton"""
        client1 = await get_elasticsearch_client()
        client2 = await get_elasticsearch_client()

        assert client1 is client2
        assert client1.is_connected is True
