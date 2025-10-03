"""
Language learning validation schemas
Vocabulary, practice sessions, and learning progress tracking
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re


class CEFRLevel(str, Enum):
    """CEFR language proficiency levels"""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class PracticeType(str, Enum):
    """Types of practice exercises"""
    FLASHCARD = "flashcard"
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    TRANSLATION = "translation"
    LISTENING = "listening"
    SPEAKING = "speaking"


class VocabularyWordRequest(BaseModel):
    """Request to add a new vocabulary word"""
    word: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Spanish word or phrase"
    )
    translation: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="English translation"
    )
    category_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="Vocabulary category ID"
    )
    difficulty_level: CEFRLevel = Field(
        default=CEFRLevel.A1,
        description="CEFR difficulty level"
    )
    example_sentence: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Example sentence using the word"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Additional notes or context"
    )

    @field_validator('word', 'translation')
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Sanitize text inputs"""
        # Remove extra whitespace
        v = ' '.join(v.split())

        # Check for invalid characters or scripts
        if re.search(r'[<>{}]', v):
            raise ValueError("Text contains invalid characters")

        return v

    @field_validator('example_sentence', 'notes')
    @classmethod
    def sanitize_optional_text(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize optional text inputs"""
        if v is None:
            return v

        # Remove extra whitespace
        v = ' '.join(v.split())

        # Check for XSS patterns
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*='
        ]

        for pattern in xss_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Text contains potentially malicious content")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "word": "aprender",
                "translation": "to learn",
                "category_id": 1,
                "difficulty_level": "A1",
                "example_sentence": "Me gusta aprender español.",
                "notes": "Regular -er verb"
            }
        }
    )


class VocabularyWordResponse(BaseModel):
    """Response model for vocabulary word"""
    id: int
    word: str
    translation: str
    category: Optional[str] = None
    difficulty_level: str
    frequency: float = Field(..., ge=0.0, description="Word frequency score")
    example_sentence: Optional[str] = None
    phonetic: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "word": "aprender",
                "translation": "to learn",
                "category": "Verbs",
                "difficulty_level": "A1",
                "frequency": 0.85,
                "example_sentence": "Me gusta aprender español.",
                "phonetic": "/a.pɾenˈdeɾ/",
                "created_at": "2025-10-03T12:00:00Z"
            }
        }
    )


class PracticeSessionRequest(BaseModel):
    """Request to start a practice session"""
    category_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="Vocabulary category to practice"
    )
    difficulty_level: Optional[CEFRLevel] = Field(
        default=None,
        description="CEFR level to practice"
    )
    num_words: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of words to practice (1-50)"
    )
    practice_type: PracticeType = Field(
        default=PracticeType.FLASHCARD,
        description="Type of practice exercise"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category_id": 1,
                "difficulty_level": "A2",
                "num_words": 10,
                "practice_type": "flashcard"
            }
        }
    )


class PracticeResultRequest(BaseModel):
    """Request to record a practice result"""
    word_id: int = Field(..., ge=1, description="Vocabulary word ID")
    correct: bool = Field(..., description="Whether answer was correct")
    response_time: float = Field(
        ...,
        ge=0.0,
        le=300.0,
        description="Response time in seconds (max 5 minutes)"
    )
    practice_type: PracticeType = Field(..., description="Type of practice")

    @field_validator('response_time')
    @classmethod
    def validate_response_time(cls, v: float) -> float:
        """Ensure response time is reasonable"""
        if v < 0.1:
            raise ValueError("Response time too short")
        if v > 300:
            raise ValueError("Response time exceeds maximum (5 minutes)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "word_id": 1,
                "correct": True,
                "response_time": 3.5,
                "practice_type": "flashcard"
            }
        }
    )


class LearningProgressResponse(BaseModel):
    """Response model for learning progress"""
    total_words_learned: int = Field(..., ge=0)
    words_mastered: int = Field(..., ge=0)
    current_streak: int = Field(..., ge=0, description="Days of continuous practice")
    total_practice_time: float = Field(..., ge=0.0, description="Total practice time in minutes")
    accuracy_rate: float = Field(..., ge=0.0, le=1.0, description="Overall accuracy (0-1)")
    level_distribution: Dict[str, int] = Field(
        ...,
        description="Distribution of words by CEFR level"
    )
    recent_sessions: List[Dict[str, Any]] = Field(
        ...,
        description="Recent practice sessions"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_words_learned": 342,
                "words_mastered": 156,
                "current_streak": 7,
                "total_practice_time": 125.5,
                "accuracy_rate": 0.78,
                "level_distribution": {
                    "A1": 120,
                    "A2": 95,
                    "B1": 78,
                    "B2": 49,
                    "C1": 0,
                    "C2": 0
                },
                "recent_sessions": [
                    {
                        "id": 1,
                        "date": "2025-10-03T12:00:00Z",
                        "type": "flashcard",
                        "accuracy": 0.85,
                        "duration": 15.5
                    }
                ]
            }
        }
    )


class PracticeSessionResponse(BaseModel):
    """Response when starting a practice session"""
    session_id: int
    words: List[Dict[str, Any]]
    total: int
    practice_type: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": 1,
                "words": [
                    {
                        "id": 1,
                        "word": "aprender",
                        "translation": "to learn",
                        "example": "Me gusta aprender español.",
                        "difficulty": "A1"
                    }
                ],
                "total": 10,
                "practice_type": "flashcard"
            }
        }
    )


class CategoryResponse(BaseModel):
    """Vocabulary category information"""
    id: int
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(default=None, max_length=200)
    word_count: int = Field(..., ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Common Verbs",
                "description": "Most frequently used Spanish verbs",
                "word_count": 150
            }
        }
    )
