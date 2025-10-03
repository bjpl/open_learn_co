"""
Vocabulary Index Configuration

Elasticsearch index for Spanish language learning vocabulary with:
- Lemma and definition search
- Difficulty level filtering
- Part of speech tagging
- Colombian regional variants
- Frequency-based ranking
"""

from typing import Dict, Any


# Vocabulary index mappings
VOCABULARY_MAPPINGS: Dict[str, Any] = {
    "properties": {
        "lemma": {
            "type": "text",
            "analyzer": "standard",
            "fields": {
                "keyword": {
                    "type": "keyword"
                },
                "raw": {
                    "type": "keyword",
                    "normalizer": "lowercase_normalizer"
                }
            }
        },
        "definition": {
            "type": "text",
            "analyzer": "spanish"
        },
        "translations": {
            "type": "text",
            "analyzer": "english"
        },
        "difficulty_level": {
            "type": "keyword"
        },
        "part_of_speech": {
            "type": "keyword"
        },
        "example_sentences": {
            "type": "text",
            "analyzer": "spanish"
        },
        "frequency_rank": {
            "type": "integer"
        },
        "regional_variant": {
            "type": "keyword"
        },
        "synonyms": {
            "type": "keyword"
        },
        "antonyms": {
            "type": "keyword"
        },
        "conjugations": {
            "type": "object",
            "enabled": False  # Store as-is without indexing
        },
        "etymology": {
            "type": "text",
            "analyzer": "standard"
        },
        "usage_notes": {
            "type": "text",
            "analyzer": "spanish"
        },
        "audio_url": {
            "type": "keyword"
        },
        "image_url": {
            "type": "keyword"
        },
        "created_at": {
            "type": "date"
        },
        "updated_at": {
            "type": "date"
        }
    }
}


# Vocabulary index settings
VOCABULARY_SETTINGS: Dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "analysis": {
        "normalizer": {
            "lowercase_normalizer": {
                "type": "custom",
                "filter": ["lowercase", "asciifolding"]
            }
        }
    },
    "max_result_window": 10000
}


# Complete index configuration
VOCABULARY_INDEX_CONFIG: Dict[str, Any] = {
    "index_name": "vocabulary",
    "mappings": VOCABULARY_MAPPINGS,
    "settings": VOCABULARY_SETTINGS
}
