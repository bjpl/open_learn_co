"""
Search Health Endpoints

Health checks and monitoring for Elasticsearch
"""

from fastapi import APIRouter
from typing import Dict, Any

from app.search.elasticsearch_client import get_elasticsearch_client

router = APIRouter()


@router.get("/health/elasticsearch")
async def elasticsearch_health() -> Dict[str, Any]:
    """
    Elasticsearch health check

    Returns cluster health, connection status, and metrics
    """
    try:
        client = await get_elasticsearch_client()
        health = await client.health_check()

        return {
            "status": "healthy" if health.get("healthy") else "unhealthy",
            "details": health
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/health/search-indices")
async def search_indices_health() -> Dict[str, Any]:
    """
    Check health of all search indices

    Returns status of articles, vocabulary, and analysis indices
    """
    try:
        client = await get_elasticsearch_client()

        indices_status = {}
        for index in ["articles", "vocabulary", "analysis"]:
            exists = await client.index_exists(index)
            indices_status[index] = {
                "exists": exists,
                "status": "ready" if exists else "not_initialized"
            }

        all_ready = all(status["exists"] for status in indices_status.values())

        return {
            "status": "healthy" if all_ready else "degraded",
            "indices": indices_status
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
