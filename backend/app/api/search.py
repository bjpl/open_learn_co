"""
Search API Endpoints

Provides RESTful API for search operations:
- Main search endpoint
- Autocomplete suggestions
- Facets for filtering
- Article-specific search
- Vocabulary search
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.services.search_service import get_search_service
from app.services.indexer_service import get_indexer_service

router = APIRouter()


# Request/Response Models
class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query string")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Results per page")
    sort_by: str = Field("_score", description="Sort field")


class SearchResponse(BaseModel):
    """Search response model"""
    hits: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    aggregations: Optional[Dict[str, Any]] = None


class AutocompleteResponse(BaseModel):
    """Autocomplete response model"""
    suggestions: List[str]


class FacetsResponse(BaseModel):
    """Facets response model"""
    facets: Dict[str, List[Dict[str, Any]]]


class IndexInitRequest(BaseModel):
    """Index initialization request"""
    recreate: bool = Field(False, description="Delete existing indices first")


class IndexArticleRequest(BaseModel):
    """Index article request"""
    article: Dict[str, Any] = Field(..., description="Article to index")


class IndexArticlesBulkRequest(BaseModel):
    """Bulk index articles request"""
    articles: List[Dict[str, Any]] = Field(..., description="Articles to index")
    refresh: bool = Field(False, description="Refresh index after indexing")


# Search Endpoints
@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> Dict[str, Any]:
    """
    Main search endpoint with full-text search and filters

    Supports:
    - Multi-field search (title, content, summary)
    - Filters (source, category, date, sentiment, difficulty)
    - Pagination
    - Sorting
    - Aggregations for faceted search
    """
    try:
        service = get_search_service()
        results = await service.search_articles(
            query=request.query,
            filters=request.filters,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by
        )
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/suggest", response_model=AutocompleteResponse)
async def autocomplete(
    query: str = Query(..., min_length=2, description="Partial query"),
    field: str = Query("title", description="Field to search"),
    size: int = Query(5, ge=1, le=10, description="Number of suggestions")
) -> Dict[str, Any]:
    """
    Autocomplete suggestions endpoint

    Returns suggestions based on partial query matching
    """
    try:
        service = get_search_service()
        suggestions = await service.autocomplete(
            query=query,
            field=field,
            size=size
        )
        return {"suggestions": suggestions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")


@router.get("/search/facets", response_model=FacetsResponse)
async def get_facets(
    index: str = Query("articles", description="Index to query (articles, vocabulary)")
) -> Dict[str, Any]:
    """
    Get available facets for filtering

    Returns all available filter options with counts
    """
    try:
        service = get_search_service()
        facets = await service.get_facets(index=index)
        return {"facets": facets}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get facets: {str(e)}")


@router.post("/search/articles", response_model=SearchResponse)
async def search_articles(request: SearchRequest) -> Dict[str, Any]:
    """
    Article-specific search endpoint

    Same as main search but explicitly for articles
    """
    return await search(request)


@router.post("/search/vocabulary")
async def search_vocabulary(
    query: str = Query(..., description="Search query"),
    difficulty_level: Optional[str] = Query(None, description="Difficulty level filter"),
    part_of_speech: Optional[str] = Query(None, description="Part of speech filter"),
    regional_variant: Optional[str] = Query(None, description="Regional variant filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Vocabulary search endpoint

    Search Spanish vocabulary with filters
    """
    try:
        service = get_search_service()

        filters = {}
        if difficulty_level:
            filters["difficulty_level"] = difficulty_level
        if part_of_speech:
            filters["part_of_speech"] = part_of_speech
        if regional_variant:
            filters["regional_variant"] = regional_variant

        results = await service.search_vocabulary(
            query=query,
            filters=filters if filters else None,
            page=page,
            page_size=page_size
        )
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vocabulary search failed: {str(e)}")


# Admin/Management Endpoints
@router.post("/search/admin/init-indices")
async def initialize_indices(request: IndexInitRequest) -> Dict[str, Any]:
    """
    Initialize Elasticsearch indices

    Admin endpoint to create or recreate indices
    """
    try:
        service = get_indexer_service()
        results = await service.initialize_indices(recreate=request.recreate)
        return {
            "status": "success",
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index initialization failed: {str(e)}")


@router.post("/search/admin/index-article")
async def index_article(request: IndexArticleRequest) -> Dict[str, Any]:
    """
    Index a single article

    Admin endpoint for real-time indexing
    """
    try:
        service = get_indexer_service()
        success = await service.index_article(request.article)
        return {
            "status": "success" if success else "failed",
            "article_id": request.article.get("id")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Article indexing failed: {str(e)}")


@router.post("/search/admin/index-articles-bulk")
async def index_articles_bulk(request: IndexArticlesBulkRequest) -> Dict[str, Any]:
    """
    Bulk index articles

    Admin endpoint for batch indexing
    """
    try:
        service = get_indexer_service()
        result = await service.index_articles_bulk(
            articles=request.articles,
            refresh=request.refresh
        )
        return {
            "status": "completed",
            "indexed": result["success"],
            "errors": len(result.get("errors", []))
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk indexing failed: {str(e)}")


@router.delete("/search/admin/article/{article_id}")
async def delete_article(article_id: str) -> Dict[str, Any]:
    """
    Delete an article from index

    Admin endpoint for removing indexed articles
    """
    try:
        service = get_indexer_service()
        success = await service.delete_article(article_id)
        return {
            "status": "success" if success else "failed",
            "article_id": article_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Article deletion failed: {str(e)}")


@router.post("/search/admin/reindex-all")
async def reindex_all() -> Dict[str, Any]:
    """
    Reindex all data from database

    Admin endpoint for full reindex operation
    """
    try:
        service = get_indexer_service()
        stats = await service.reindex_all()
        return {
            "status": "completed",
            "statistics": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")
