"""
Search Service

Provides high-level search operations including:
- Full-text search with highlighting
- Faceted search and aggregations
- Autocomplete suggestions
- Fuzzy matching for typos
- Multi-field search
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


class SearchService:
    """Service for executing Elasticsearch queries"""

    def __init__(self):
        self.articles_index = ARTICLES_INDEX_CONFIG["index_name"]
        self.vocabulary_index = VOCABULARY_INDEX_CONFIG["index_name"]
        self.analysis_index = ANALYSIS_INDEX_CONFIG["index_name"]

    async def search_articles(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "_score"
    ) -> Dict[str, Any]:
        """
        Search articles with full-text search and filters

        Args:
            query: Search query string
            filters: Optional filters (source, category, date_range, sentiment, difficulty)
            page: Page number (1-based)
            page_size: Results per page
            sort_by: Sort field (_score, published_date, relevance)

        Returns:
            Search results with hits, total, and aggregations
        """
        client = await get_elasticsearch_client()

        # Build query
        must_clauses = []
        filter_clauses = []

        # Multi-field search with boosting
        if query:
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",      # Title gets 3x boost
                        "content",      # Content gets 1x boost
                        "summary^2"     # Summary gets 2x boost
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        else:
            must_clauses.append({"match_all": {}})

        # Apply filters
        if filters:
            # Source filter
            if "source" in filters and filters["source"]:
                filter_clauses.append({
                    "terms": {"source": filters["source"] if isinstance(filters["source"], list) else [filters["source"]]}
                })

            # Category filter
            if "category" in filters and filters["category"]:
                filter_clauses.append({
                    "terms": {"category": filters["category"] if isinstance(filters["category"], list) else [filters["category"]]}
                })

            # Date range filter
            if "date_from" in filters or "date_to" in filters:
                date_range: Dict[str, Any] = {}
                if "date_from" in filters:
                    date_range["gte"] = filters["date_from"]
                if "date_to" in filters:
                    date_range["lte"] = filters["date_to"]
                filter_clauses.append({
                    "range": {"published_date": date_range}
                })

            # Sentiment filter
            if "sentiment" in filters and filters["sentiment"]:
                filter_clauses.append({
                    "terms": {"sentiment_label": filters["sentiment"] if isinstance(filters["sentiment"], list) else [filters["sentiment"]]}
                })

            # Difficulty level filter
            if "difficulty_level" in filters and filters["difficulty_level"]:
                filter_clauses.append({
                    "terms": {"difficulty_level": filters["difficulty_level"] if isinstance(filters["difficulty_level"], list) else [filters["difficulty_level"]]}
                })

        # Build complete query
        es_query: Dict[str, Any] = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        }

        # Build sort
        sort: List[Dict[str, Any]] = []
        if sort_by == "published_date":
            sort.append({"published_date": {"order": "desc"}})
        elif sort_by == "relevance":
            sort.append("_score")
        else:
            sort.append("_score")

        # Calculate pagination
        from_ = (page - 1) * page_size

        # Add aggregations for faceted search
        aggregations = {
            "sources": {
                "terms": {"field": "source", "size": 20}
            },
            "categories": {
                "terms": {"field": "category", "size": 20}
            },
            "sentiment": {
                "terms": {"field": "sentiment_label"}
            },
            "difficulty": {
                "terms": {"field": "difficulty_level"}
            },
            "top_entities": {
                "nested": {"path": "entities"},
                "aggs": {
                    "entity_names": {
                        "terms": {"field": "entities.name.keyword", "size": 10}
                    }
                }
            }
        }

        # Execute search
        body: Dict[str, Any] = {
            "query": es_query,
            "size": page_size,
            "from": from_,
            "sort": sort,
            "aggs": aggregations,
            "highlight": {
                "fields": {
                    "title": {"number_of_fragments": 0},
                    "content": {"fragment_size": 150, "number_of_fragments": 3},
                    "summary": {"number_of_fragments": 0}
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }

        response = await client.search(
            index_name=self.articles_index,
            query=es_query,
            size=page_size,
            from_=from_,
            sort=sort
        )

        # Format response
        hits = []
        for hit in response["hits"]["hits"]:
            result = {
                "id": hit["_id"],
                "score": hit["_score"],
                **hit["_source"]
            }

            # Add highlights if available
            if "highlight" in hit:
                result["highlights"] = hit["highlight"]

            hits.append(result)

        return {
            "hits": hits,
            "total": response["hits"]["total"]["value"],
            "page": page,
            "page_size": page_size,
            "total_pages": (response["hits"]["total"]["value"] + page_size - 1) // page_size,
            "aggregations": response.get("aggregations", {})
        }

    async def autocomplete(
        self,
        query: str,
        field: str = "title",
        size: int = 5
    ) -> List[str]:
        """
        Get autocomplete suggestions

        Args:
            query: Partial query string
            field: Field to search (title, content)
            size: Number of suggestions

        Returns:
            List of suggestions
        """
        client = await get_elasticsearch_client()

        es_query = {
            "match": {
                f"{field}.autocomplete": {
                    "query": query,
                    "operator": "and"
                }
            }
        }

        response = await client.search(
            index_name=self.articles_index,
            query=es_query,
            size=size
        )

        suggestions = []
        for hit in response["hits"]["hits"]:
            if field in hit["_source"]:
                suggestions.append(hit["_source"][field])

        return suggestions

    async def search_vocabulary(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search vocabulary with filters

        Args:
            query: Search query
            filters: Optional filters (difficulty_level, part_of_speech, regional_variant)
            page: Page number
            page_size: Results per page

        Returns:
            Search results
        """
        client = await get_elasticsearch_client()

        # Build query
        must_clauses = []
        filter_clauses = []

        if query:
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "lemma^3",
                        "definition^2",
                        "translations",
                        "example_sentences"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        else:
            must_clauses.append({"match_all": {}})

        # Apply filters
        if filters:
            if "difficulty_level" in filters:
                filter_clauses.append({
                    "term": {"difficulty_level": filters["difficulty_level"]}
                })

            if "part_of_speech" in filters:
                filter_clauses.append({
                    "term": {"part_of_speech": filters["part_of_speech"]}
                })

            if "regional_variant" in filters:
                filter_clauses.append({
                    "term": {"regional_variant": filters["regional_variant"]}
                })

        es_query: Dict[str, Any] = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        }

        # Calculate pagination
        from_ = (page - 1) * page_size

        # Sort by frequency rank (lower is better)
        sort = [{"frequency_rank": {"order": "asc"}}, "_score"]

        response = await client.search(
            index_name=self.vocabulary_index,
            query=es_query,
            size=page_size,
            from_=from_,
            sort=sort
        )

        hits = []
        for hit in response["hits"]["hits"]:
            hits.append({
                "id": hit["_id"],
                "score": hit["_score"],
                **hit["_source"]
            })

        return {
            "hits": hits,
            "total": response["hits"]["total"]["value"],
            "page": page,
            "page_size": page_size,
            "total_pages": (response["hits"]["total"]["value"] + page_size - 1) // page_size
        }

    async def get_facets(self, index: str = "articles") -> Dict[str, Any]:
        """
        Get available facets for filtering

        Args:
            index: Index to query (articles, vocabulary)

        Returns:
            Available facets with counts
        """
        client = await get_elasticsearch_client()

        index_name = self.articles_index if index == "articles" else self.vocabulary_index

        # Build aggregations based on index
        if index == "articles":
            aggs = {
                "sources": {"terms": {"field": "source", "size": 50}},
                "categories": {"terms": {"field": "category", "size": 50}},
                "sentiment": {"terms": {"field": "sentiment_label"}},
                "difficulty": {"terms": {"field": "difficulty_level"}}
            }
        else:  # vocabulary
            aggs = {
                "difficulty": {"terms": {"field": "difficulty_level"}},
                "part_of_speech": {"terms": {"field": "part_of_speech", "size": 20}},
                "regional_variant": {"terms": {"field": "regional_variant", "size": 10}}
            }

        response = await client.search(
            index_name=index_name,
            query={"match_all": {}},
            size=0  # Don't return documents, only aggregations
        )

        # Format aggregations
        facets = {}
        if "aggregations" in response:
            for key, agg in response["aggregations"].items():
                if "buckets" in agg:
                    facets[key] = [
                        {"value": bucket["key"], "count": bucket["doc_count"]}
                        for bucket in agg["buckets"]
                    ]

        return facets


# Global service instance
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """Get search service singleton"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
