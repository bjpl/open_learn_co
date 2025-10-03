"""
Elasticsearch Index Definitions

Defines index schemas for:
- Articles (news content)
- Vocabulary (language learning)
- Analysis (NLP results)
"""

from .articles_index import ARTICLES_INDEX_CONFIG
from .vocabulary_index import VOCABULARY_INDEX_CONFIG
from .analysis_index import ANALYSIS_INDEX_CONFIG

__all__ = [
    "ARTICLES_INDEX_CONFIG",
    "VOCABULARY_INDEX_CONFIG",
    "ANALYSIS_INDEX_CONFIG",
]
