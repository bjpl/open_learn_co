"""
Text and intelligence analysis validation schemas
Includes sentiment, entity extraction, and topic modeling
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import re


class AnalysisType(str, Enum):
    """Types of analysis available"""
    SENTIMENT = "sentiment"
    ENTITIES = "entities"
    TOPICS = "topics"
    DIFFICULTY = "difficulty"
    SUMMARY = "summary"
    ALL = "all"


class LanguageCode(str, Enum):
    """Supported language codes"""
    ES = "es"
    EN = "en"


class AnalysisRequest(BaseModel):
    """Request for text analysis"""
    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Text to analyze (10-50,000 characters)"
    )
    analysis_types: List[AnalysisType] = Field(
        default=[AnalysisType.SENTIMENT, AnalysisType.ENTITIES, AnalysisType.TOPICS, AnalysisType.DIFFICULTY],
        description="Types of analysis to perform"
    )
    language: LanguageCode = Field(
        default=LanguageCode.ES,
        description="Language code (es or en)"
    )

    @field_validator('text')
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Sanitize input text"""
        # Remove null bytes
        v = v.replace('\x00', '')

        # Check for XSS patterns
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onload\s*='
        ]

        for pattern in xss_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Text contains potentially malicious content")

        return v

    @field_validator('analysis_types')
    @classmethod
    def validate_analysis_types(cls, v: List[AnalysisType]) -> List[AnalysisType]:
        """Ensure at least one analysis type is selected"""
        if not v:
            raise ValueError("At least one analysis type must be selected")

        # If 'all' is selected, expand to all types
        if AnalysisType.ALL in v:
            return [AnalysisType.SENTIMENT, AnalysisType.ENTITIES,
                    AnalysisType.TOPICS, AnalysisType.DIFFICULTY, AnalysisType.SUMMARY]

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "El Congreso de Colombia aprobó una nueva reforma política que busca fortalecer la democracia y aumentar la participación ciudadana en los procesos electorales.",
                "analysis_types": ["sentiment", "entities", "topics"],
                "language": "es"
            }
        }
    )


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis of multiple contents"""
    content_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of content IDs to analyze (1-100 items)"
    )
    analysis_types: List[AnalysisType] = Field(
        default=[AnalysisType.SENTIMENT, AnalysisType.ENTITIES, AnalysisType.TOPICS],
        description="Types of analysis to perform"
    )

    @field_validator('content_ids')
    @classmethod
    def validate_content_ids(cls, v: List[int]) -> List[int]:
        """Validate content IDs are positive integers"""
        if not v:
            raise ValueError("At least one content ID must be provided")

        if len(v) > 100:
            raise ValueError("Maximum 100 content IDs allowed per batch")

        for id_val in v:
            if id_val <= 0:
                raise ValueError("Content IDs must be positive integers")

        # Remove duplicates
        return list(set(v))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content_ids": [1, 2, 3, 4, 5],
                "analysis_types": ["sentiment", "entities"]
            }
        }
    )


class SentimentResult(BaseModel):
    """Sentiment analysis result"""
    polarity: float = Field(..., ge=-1.0, le=1.0, description="Sentiment polarity (-1 to 1)")
    subjectivity: float = Field(..., ge=0.0, le=1.0, description="Subjectivity score (0 to 1)")
    classification: str = Field(..., description="Sentiment classification (positive/negative/neutral)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "polarity": 0.65,
                "subjectivity": 0.45,
                "classification": "positive",
                "confidence": 0.82
            }
        }
    )


class EntityResult(BaseModel):
    """Named entity extraction result"""
    text: str = Field(..., description="Entity text")
    type: str = Field(..., description="Entity type (PERSON, ORG, LOC, etc.)")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Confidence score")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Congreso de Colombia",
                "type": "ORG",
                "confidence": 0.95
            }
        }
    )


class TopicResult(BaseModel):
    """Topic modeling result"""
    topic_id: int = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name/label")
    probability: float = Field(..., ge=0.0, le=1.0, description="Topic probability")
    keywords: List[str] = Field(..., description="Topic keywords")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic_id": 0,
                "topic_name": "Politics",
                "probability": 0.78,
                "keywords": ["congreso", "política", "elecciones", "reforma"]
            }
        }
    )


class DifficultyResult(BaseModel):
    """Text difficulty scoring result"""
    score: float = Field(..., ge=0.0, le=1.0, description="Difficulty score (0=easy, 1=hard)")
    cefr_level: str = Field(..., description="CEFR level (A1, A2, B1, B2, C1, C2)")
    reading_time: float = Field(..., ge=0.0, description="Estimated reading time in minutes")
    flesch_score: float = Field(..., description="Flesch reading ease score")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "score": 0.65,
                "cefr_level": "B2",
                "reading_time": 3.5,
                "flesch_score": 55.2
            }
        }
    )


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    id: Optional[int] = None
    text_preview: str = Field(..., description="Preview of analyzed text")
    sentiment: Optional[SentimentResult] = None
    entities: Optional[List[EntityResult]] = None
    topics: Optional[List[TopicResult]] = None
    difficulty: Optional[DifficultyResult] = None
    summary: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "text_preview": "El Congreso de Colombia aprobó una nueva reforma...",
                "sentiment": {
                    "polarity": 0.65,
                    "subjectivity": 0.45,
                    "classification": "positive",
                    "confidence": 0.82
                },
                "entities": [
                    {"text": "Congreso de Colombia", "type": "ORG", "confidence": 0.95}
                ],
                "topics": [
                    {
                        "topic_id": 0,
                        "topic_name": "Politics",
                        "probability": 0.78,
                        "keywords": ["congreso", "política"]
                    }
                ],
                "difficulty": {
                    "score": 0.65,
                    "cefr_level": "B2",
                    "reading_time": 3.5,
                    "flesch_score": 55.2
                },
                "summary": "Reforma política aprobada por el Congreso",
                "created_at": "2025-10-03T12:00:00Z"
            }
        }
    )


class AnalysisStatistics(BaseModel):
    """Analysis statistics and aggregations"""
    total_analyses: int
    average_sentiment: float = Field(..., ge=-1.0, le=1.0)
    entity_distribution: Dict[str, int]
    last_analysis: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_analyses": 15234,
                "average_sentiment": 0.23,
                "entity_distribution": {
                    "PERSON": 3421,
                    "ORG": 2134,
                    "LOC": 1823
                },
                "last_analysis": "2025-10-03T12:00:00Z"
            }
        }
    )
