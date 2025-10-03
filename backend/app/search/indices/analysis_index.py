"""
Analysis Index Configuration

Elasticsearch index for NLP analysis results with:
- Analysis type filtering
- Confidence scoring
- Temporal tracking
- Result caching
"""

from typing import Dict, Any


# Analysis index mappings
ANALYSIS_MAPPINGS: Dict[str, Any] = {
    "properties": {
        "content_id": {
            "type": "keyword"
        },
        "content_type": {
            "type": "keyword"
        },
        "analysis_type": {
            "type": "keyword"
        },
        "results": {
            "type": "object",
            "enabled": True
        },
        "confidence_score": {
            "type": "float"
        },
        "processing_time_ms": {
            "type": "integer"
        },
        "model_version": {
            "type": "keyword"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "keyword"
                },
                "language": {
                    "type": "keyword"
                },
                "word_count": {
                    "type": "integer"
                }
            }
        },
        "created_at": {
            "type": "date"
        },
        "expires_at": {
            "type": "date"
        }
    }
}


# Analysis index settings
ANALYSIS_SETTINGS: Dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 0,  # Analysis results can be regenerated
    "max_result_window": 10000
}


# Complete index configuration
ANALYSIS_INDEX_CONFIG: Dict[str, Any] = {
    "index_name": "analysis",
    "mappings": ANALYSIS_MAPPINGS,
    "settings": ANALYSIS_SETTINGS
}
