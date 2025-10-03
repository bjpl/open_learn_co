"""
Articles Index Configuration

Elasticsearch index for Colombian news articles with:
- Colombian Spanish analyzer
- Full-text search on title, content, summary
- Filters for source, category, date, sentiment
- Entity and topic extraction support
"""

from typing import Dict, Any


# Colombian Spanish analyzer configuration
COLOMBIAN_SPANISH_ANALYZER: Dict[str, Any] = {
    "analyzer": {
        "colombian_spanish": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "lowercase",
                "spanish_stop",
                "spanish_stemmer",
                "asciifolding",
                "elision"
            ]
        },
        "colombian_autocomplete": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
                "lowercase",
                "autocomplete_filter",
                "asciifolding"
            ]
        }
    },
    "filter": {
        "spanish_stop": {
            "type": "stop",
            "stopwords": "_spanish_"
        },
        "spanish_stemmer": {
            "type": "stemmer",
            "language": "spanish"
        },
        "elision": {
            "type": "elision",
            "articles": ["el", "la", "los", "las", "un", "una", "unos", "unas"]
        },
        "autocomplete_filter": {
            "type": "edge_ngram",
            "min_gram": 2,
            "max_gram": 20
        }
    }
}


# Articles index mappings
ARTICLES_MAPPINGS: Dict[str, Any] = {
    "properties": {
        "title": {
            "type": "text",
            "analyzer": "colombian_spanish",
            "fields": {
                "keyword": {
                    "type": "keyword"
                },
                "autocomplete": {
                    "type": "text",
                    "analyzer": "colombian_autocomplete"
                }
            }
        },
        "content": {
            "type": "text",
            "analyzer": "colombian_spanish"
        },
        "summary": {
            "type": "text",
            "analyzer": "colombian_spanish"
        },
        "source": {
            "type": "keyword"
        },
        "category": {
            "type": "keyword"
        },
        "published_date": {
            "type": "date"
        },
        "scraped_date": {
            "type": "date"
        },
        "sentiment_score": {
            "type": "float"
        },
        "sentiment_label": {
            "type": "keyword"
        },
        "entities": {
            "type": "nested",
            "properties": {
                "name": {
                    "type": "text",
                    "analyzer": "colombian_spanish",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "type": {
                    "type": "keyword"
                },
                "confidence": {
                    "type": "float"
                }
            }
        },
        "topics": {
            "type": "keyword"
        },
        "difficulty_level": {
            "type": "keyword"
        },
        "url": {
            "type": "keyword"
        },
        "image_url": {
            "type": "keyword"
        },
        "author": {
            "type": "text",
            "analyzer": "colombian_spanish",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        },
        "word_count": {
            "type": "integer"
        },
        "reading_time_minutes": {
            "type": "integer"
        },
        "language": {
            "type": "keyword"
        },
        "indexed_at": {
            "type": "date"
        }
    }
}


# Articles index settings
ARTICLES_SETTINGS: Dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "analysis": COLOMBIAN_SPANISH_ANALYZER,
    "max_result_window": 10000
}


# Complete index configuration
ARTICLES_INDEX_CONFIG: Dict[str, Any] = {
    "index_name": "articles",
    "mappings": ARTICLES_MAPPINGS,
    "settings": ARTICLES_SETTINGS
}
