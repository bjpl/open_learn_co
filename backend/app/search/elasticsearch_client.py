"""
Elasticsearch Client

Manages Elasticsearch connection and client lifecycle with:
- Connection pooling and retry logic
- Health checks and monitoring
- Index management operations
- Bulk indexing support
"""

import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch, NotFoundError, RequestError
from elasticsearch.helpers import async_bulk

from app.config.settings import settings

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """
    Elasticsearch client wrapper with connection management
    """

    def __init__(self):
        self._client: Optional[AsyncElasticsearch] = None
        self._connected: bool = False

    async def connect(self) -> None:
        """Initialize Elasticsearch connection"""
        if self._connected:
            logger.warning("Elasticsearch already connected")
            return

        try:
            # Parse credentials from URL or use separate settings
            self._client = AsyncElasticsearch(
                [settings.ELASTICSEARCH_URL],
                # Connection settings
                retry_on_timeout=True,
                max_retries=3,
                # Timeout settings
                request_timeout=30,
                # Security enabled for production
                # Credentials parsed from ELASTICSEARCH_URL (http://elastic:password@host:9200)
                # OR explicitly set via http_auth if needed
                verify_certs=getattr(settings, 'ELASTICSEARCH_VERIFY_CERTS', False),
            )

            # Test connection
            info = await self._client.info()
            self._connected = True
            logger.info(f"Connected to Elasticsearch {info['version']['number']}")

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Elasticsearch connection"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Elasticsearch")

    async def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch cluster health"""
        if not self._client:
            return {"status": "disconnected", "healthy": False}

        try:
            health = await self._client.cluster.health()
            return {
                "status": health["status"],
                "healthy": health["status"] in ["green", "yellow"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"],
                "active_shards": health["active_shards"],
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "healthy": False, "error": str(e)}

    async def create_index(
        self,
        index_name: str,
        mappings: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create an index with mappings and settings

        Args:
            index_name: Name of the index
            mappings: Index mappings
            settings: Index settings (optional)

        Returns:
            True if created, False if already exists
        """
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        try:
            # Check if index exists
            exists = await self._client.indices.exists(index=index_name)
            if exists:
                logger.warning(f"Index {index_name} already exists")
                return False

            # Create index
            body: Dict[str, Any] = {"mappings": mappings}
            if settings:
                body["settings"] = settings

            await self._client.indices.create(
                index=index_name,
                body=body
            )

            logger.info(f"Created index: {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            raise

    async def delete_index(self, index_name: str) -> bool:
        """
        Delete an index

        Args:
            index_name: Name of the index to delete

        Returns:
            True if deleted, False if not found
        """
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        try:
            await self._client.indices.delete(index=index_name)
            logger.info(f"Deleted index: {index_name}")
            return True

        except NotFoundError:
            logger.warning(f"Index {index_name} not found")
            return False

        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            raise

    async def index_exists(self, index_name: str) -> bool:
        """Check if index exists"""
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        return await self._client.indices.exists(index=index_name)

    async def refresh_index(self, index_name: str) -> None:
        """Refresh an index to make recent changes visible"""
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        await self._client.indices.refresh(index=index_name)

    async def bulk_index(
        self,
        index_name: str,
        documents: List[Dict[str, Any]],
        id_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk index documents

        Args:
            index_name: Target index
            documents: List of documents to index
            id_field: Field to use as document ID (optional)

        Returns:
            Dict with success count and errors
        """
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        if not documents:
            return {"success": 0, "errors": []}

        # Prepare bulk actions
        actions = []
        for doc in documents:
            action: Dict[str, Any] = {
                "_index": index_name,
                "_source": doc
            }

            # Use specified field as document ID
            if id_field and id_field in doc:
                action["_id"] = doc[id_field]

            actions.append(action)

        try:
            # Perform bulk indexing
            success, errors = await async_bulk(
                self._client,
                actions,
                chunk_size=1000,
                raise_on_error=False,
                raise_on_exception=False
            )

            logger.info(f"Bulk indexed {success} documents to {index_name}")

            if errors:
                logger.warning(f"Bulk indexing had {len(errors)} errors")

            return {
                "success": success,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            raise

    async def update_document(
        self,
        index_name: str,
        doc_id: str,
        document: Dict[str, Any]
    ) -> None:
        """Update a document by ID"""
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        await self._client.update(
            index=index_name,
            id=doc_id,
            body={"doc": document}
        )

    async def delete_document(
        self,
        index_name: str,
        doc_id: str
    ) -> None:
        """Delete a document by ID"""
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        await self._client.delete(
            index=index_name,
            id=doc_id
        )

    async def search(
        self,
        index_name: str,
        query: Dict[str, Any],
        size: int = 10,
        from_: int = 0,
        sort: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Execute a search query

        Args:
            index_name: Index to search
            query: Elasticsearch query DSL
            size: Number of results to return
            from_: Offset for pagination
            sort: Sort criteria

        Returns:
            Search results
        """
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        body: Dict[str, Any] = {
            "query": query,
            "size": size,
            "from": from_
        }

        if sort:
            body["sort"] = sort

        return await self._client.search(
            index=index_name,
            body=body
        )

    @property
    def client(self) -> AsyncElasticsearch:
        """Get the underlying Elasticsearch client"""
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected


# Global client instance
_es_client: Optional[ElasticsearchClient] = None


async def get_elasticsearch_client() -> ElasticsearchClient:
    """Get or create Elasticsearch client singleton"""
    global _es_client

    if _es_client is None:
        _es_client = ElasticsearchClient()
        await _es_client.connect()

    return _es_client


@asynccontextmanager
async def elasticsearch_session():
    """Context manager for Elasticsearch operations"""
    client = await get_elasticsearch_client()
    try:
        yield client
    finally:
        pass  # Don't disconnect, keep connection alive
