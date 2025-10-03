"""
Elasticsearch Search Module

Provides full-text search capabilities for Colombian content including:
- News articles search
- Vocabulary search
- NLP analysis search
- Colombian Spanish language support
"""

from .elasticsearch_client import ElasticsearchClient, get_elasticsearch_client

__all__ = ["ElasticsearchClient", "get_elasticsearch_client"]
