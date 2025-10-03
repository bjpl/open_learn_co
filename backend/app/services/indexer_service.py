"""
Indexer Service

Manages index synchronization and updates including:
- Real-time indexing on data changes
- Bulk reindexing utilities
- Index optimization
- Automatic index updates
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.search.elasticsearch_client import get_elasticsearch_client
from app.search.indices import (
    ARTICLES_INDEX_CONFIG,
    VOCABULARY_INDEX_CONFIG,
    ANALYSIS_INDEX_CONFIG
)

logger = logging.getLogger(__name__)


class IndexerService:
    """Service for managing Elasticsearch index operations"""

    def __init__(self):
        self.articles_index = ARTICLES_INDEX_CONFIG["index_name"]
        self.vocabulary_index = VOCABULARY_INDEX_CONFIG["index_name"]
        self.analysis_index = ANALYSIS_INDEX_CONFIG["index_name"]

    async def initialize_indices(self, recreate: bool = False) -> Dict[str, bool]:
        """
        Initialize all Elasticsearch indices

        Args:
            recreate: If True, delete existing indices first

        Returns:
            Dict mapping index names to creation status
        """
        client = await get_elasticsearch_client()
        results = {}

        indices = [
            ARTICLES_INDEX_CONFIG,
            VOCABULARY_INDEX_CONFIG,
            ANALYSIS_INDEX_CONFIG
        ]

        for config in indices:
            index_name = config["index_name"]

            try:
                # Delete if recreate requested
                if recreate:
                    exists = await client.index_exists(index_name)
                    if exists:
                        await client.delete_index(index_name)
                        logger.info(f"Deleted existing index: {index_name}")

                # Create index
                created = await client.create_index(
                    index_name=index_name,
                    mappings=config["mappings"],
                    settings=config["settings"]
                )

                results[index_name] = created

            except Exception as e:
                logger.error(f"Failed to initialize index {index_name}: {e}")
                results[index_name] = False

        return results

    async def index_article(self, article: Dict[str, Any]) -> bool:
        """
        Index a single article

        Args:
            article: Article document to index

        Returns:
            True if successful
        """
        client = await get_elasticsearch_client()

        try:
            # Prepare document
            doc = self._prepare_article_document(article)

            # Index document
            await client.bulk_index(
                index_name=self.articles_index,
                documents=[doc],
                id_field="id"
            )

            logger.info(f"Indexed article: {doc.get('id', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to index article: {e}")
            return False

    async def index_articles_bulk(
        self,
        articles: List[Dict[str, Any]],
        refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Bulk index articles

        Args:
            articles: List of article documents
            refresh: Whether to refresh index after indexing

        Returns:
            Indexing results with success count and errors
        """
        client = await get_elasticsearch_client()

        try:
            # Prepare documents
            documents = [self._prepare_article_document(a) for a in articles]

            # Bulk index
            result = await client.bulk_index(
                index_name=self.articles_index,
                documents=documents,
                id_field="id"
            )

            # Refresh if requested
            if refresh:
                await client.refresh_index(self.articles_index)

            logger.info(f"Bulk indexed {result['success']} articles")
            return result

        except Exception as e:
            logger.error(f"Failed to bulk index articles: {e}")
            return {"success": 0, "errors": [str(e)]}

    async def index_vocabulary(self, vocab: Dict[str, Any]) -> bool:
        """
        Index a vocabulary term

        Args:
            vocab: Vocabulary document to index

        Returns:
            True if successful
        """
        client = await get_elasticsearch_client()

        try:
            # Prepare document
            doc = self._prepare_vocabulary_document(vocab)

            # Index document
            await client.bulk_index(
                index_name=self.vocabulary_index,
                documents=[doc],
                id_field="id"
            )

            logger.info(f"Indexed vocabulary: {doc.get('lemma', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to index vocabulary: {e}")
            return False

    async def index_vocabulary_bulk(
        self,
        vocabulary: List[Dict[str, Any]],
        refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Bulk index vocabulary

        Args:
            vocabulary: List of vocabulary documents
            refresh: Whether to refresh index after indexing

        Returns:
            Indexing results
        """
        client = await get_elasticsearch_client()

        try:
            # Prepare documents
            documents = [self._prepare_vocabulary_document(v) for v in vocabulary]

            # Bulk index
            result = await client.bulk_index(
                index_name=self.vocabulary_index,
                documents=documents,
                id_field="id"
            )

            # Refresh if requested
            if refresh:
                await client.refresh_index(self.vocabulary_index)

            logger.info(f"Bulk indexed {result['success']} vocabulary terms")
            return result

        except Exception as e:
            logger.error(f"Failed to bulk index vocabulary: {e}")
            return {"success": 0, "errors": [str(e)]}

    async def index_analysis(self, analysis: Dict[str, Any]) -> bool:
        """
        Index an analysis result

        Args:
            analysis: Analysis document to index

        Returns:
            True if successful
        """
        client = await get_elasticsearch_client()

        try:
            # Prepare document
            doc = self._prepare_analysis_document(analysis)

            # Index document
            await client.bulk_index(
                index_name=self.analysis_index,
                documents=[doc],
                id_field="id"
            )

            logger.info(f"Indexed analysis: {doc.get('id', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to index analysis: {e}")
            return False

    async def update_article(
        self,
        article_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an article document

        Args:
            article_id: Article ID
            updates: Fields to update

        Returns:
            True if successful
        """
        client = await get_elasticsearch_client()

        try:
            await client.update_document(
                index_name=self.articles_index,
                doc_id=article_id,
                document=updates
            )

            logger.info(f"Updated article: {article_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update article {article_id}: {e}")
            return False

    async def delete_article(self, article_id: str) -> bool:
        """
        Delete an article from index

        Args:
            article_id: Article ID to delete

        Returns:
            True if successful
        """
        client = await get_elasticsearch_client()

        try:
            await client.delete_document(
                index_name=self.articles_index,
                doc_id=article_id
            )

            logger.info(f"Deleted article: {article_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete article {article_id}: {e}")
            return False

    async def reindex_all(
        self,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Reindex all data from database

        Args:
            batch_size: Number of documents per batch

        Returns:
            Reindexing statistics
        """
        # TODO: Implement fetching from database and reindexing
        # This would integrate with your database models
        logger.info("Full reindex operation started")

        stats = {
            "articles": {"total": 0, "success": 0, "errors": 0},
            "vocabulary": {"total": 0, "success": 0, "errors": 0},
            "analysis": {"total": 0, "success": 0, "errors": 0}
        }

        # Placeholder for actual implementation
        logger.warning("Full reindex not yet implemented - requires database integration")

        return stats

    def _prepare_article_document(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare article document for indexing"""
        doc = {
            "id": article.get("id"),
            "title": article.get("title", ""),
            "content": article.get("content", ""),
            "summary": article.get("summary", ""),
            "source": article.get("source", ""),
            "category": article.get("category", ""),
            "url": article.get("url", ""),
            "indexed_at": datetime.utcnow().isoformat()
        }

        # Optional fields
        if "published_date" in article:
            doc["published_date"] = article["published_date"]
        if "sentiment_score" in article:
            doc["sentiment_score"] = article["sentiment_score"]
        if "sentiment_label" in article:
            doc["sentiment_label"] = article["sentiment_label"]
        if "entities" in article:
            doc["entities"] = article["entities"]
        if "topics" in article:
            doc["topics"] = article["topics"]
        if "difficulty_level" in article:
            doc["difficulty_level"] = article["difficulty_level"]
        if "author" in article:
            doc["author"] = article["author"]
        if "word_count" in article:
            doc["word_count"] = article["word_count"]

        return doc

    def _prepare_vocabulary_document(self, vocab: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare vocabulary document for indexing"""
        doc = {
            "id": vocab.get("id"),
            "lemma": vocab.get("lemma", ""),
            "definition": vocab.get("definition", ""),
            "difficulty_level": vocab.get("difficulty_level", ""),
            "part_of_speech": vocab.get("part_of_speech", ""),
            "created_at": datetime.utcnow().isoformat()
        }

        # Optional fields
        if "translations" in vocab:
            doc["translations"] = vocab["translations"]
        if "example_sentences" in vocab:
            doc["example_sentences"] = vocab["example_sentences"]
        if "frequency_rank" in vocab:
            doc["frequency_rank"] = vocab["frequency_rank"]
        if "regional_variant" in vocab:
            doc["regional_variant"] = vocab["regional_variant"]

        return doc

    def _prepare_analysis_document(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare analysis document for indexing"""
        return {
            "id": analysis.get("id"),
            "content_id": analysis.get("content_id", ""),
            "content_type": analysis.get("content_type", ""),
            "analysis_type": analysis.get("analysis_type", ""),
            "results": analysis.get("results", {}),
            "confidence_score": analysis.get("confidence_score", 0.0),
            "created_at": datetime.utcnow().isoformat()
        }


# Global service instance
_indexer_service: Optional[IndexerService] = None


def get_indexer_service() -> IndexerService:
    """Get indexer service singleton"""
    global _indexer_service
    if _indexer_service is None:
        _indexer_service = IndexerService()
    return _indexer_service
