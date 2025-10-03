"""
Web scraping validation schemas
Includes source configuration and content filtering
"""

from pydantic import BaseModel, HttpUrl, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SourcePriority(str, Enum):
    """Source priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceCategory(str, Enum):
    """Source categories"""
    MEDIA = "media"
    GOVERNMENT = "government"
    THINK_TANKS = "think_tanks"
    ACADEMIC = "academic"
    NGO = "ngo"
    INTERNATIONAL = "international"


class ScrapingRequest(BaseModel):
    """Request to trigger scraping for a source"""
    source_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the source to scrape"
    )
    force_refresh: bool = Field(
        default=False,
        description="Force re-scraping even if recently scraped"
    )

    @field_validator('source_name')
    @classmethod
    def sanitize_source_name(cls, v: str) -> str:
        """Sanitize source name"""
        # Remove extra whitespace
        v = ' '.join(v.split())

        # Prevent path traversal
        if '../' in v or '..\\' in v:
            raise ValueError("Invalid source name")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_name": "El Tiempo",
                "force_refresh": False
            }
        }
    )


class SourceFilter(BaseModel):
    """Filter sources by category and priority"""
    category: Optional[SourceCategory] = Field(
        default=None,
        description="Filter by source category"
    )
    priority: Optional[SourcePriority] = Field(
        default=None,
        description="Filter by priority level"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "media",
                "priority": "high"
            }
        }
    )


class ContentFilter(BaseModel):
    """Filter scraped content with validation"""
    source: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Filter by source name"
    )
    category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Filter by content category"
    )
    min_difficulty: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum difficulty score (0.0-1.0)"
    )
    max_difficulty: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Maximum difficulty score (0.0-1.0)"
    )
    search_query: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Search in title and content"
    )
    start_date: Optional[datetime] = Field(
        default=None,
        description="Filter content published after this date"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Filter content published before this date"
    )
    skip: int = Field(
        default=0,
        ge=0,
        le=10000,
        description="Number of records to skip"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum records to return"
    )

    @field_validator('search_query')
    @classmethod
    def sanitize_search_query(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize search query"""
        if v is None:
            return v

        # Remove SQL injection patterns
        dangerous_patterns = [
            '--', ';--', '/*', '*/', 'xp_', 'sp_',
            'union', 'select', 'insert', 'update', 'delete'
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Search query contains forbidden pattern: {pattern}")

        return v

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_dates(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure dates are valid"""
        if v and v > datetime.utcnow():
            raise ValueError("Date cannot be in the future")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "El Tiempo",
                "category": "politics",
                "min_difficulty": 0.3,
                "max_difficulty": 0.7,
                "search_query": "elecciones",
                "skip": 0,
                "limit": 20
            }
        }
    )


class ScrapedContentResponse(BaseModel):
    """Response model for scraped content"""
    id: int
    source: str
    source_url: str
    category: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    content: str
    author: Optional[str] = None
    word_count: int
    published_date: Optional[datetime] = None
    scraped_at: datetime
    difficulty_score: Optional[float] = None
    tags: Optional[List[str]] = None
    colombian_entities: Optional[List[str]] = None
    is_paywall: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "source": "El Tiempo",
                "source_url": "https://www.eltiempo.com/article/123",
                "category": "politics",
                "title": "Nueva reforma política en Colombia",
                "subtitle": "El Congreso debate cambios constitucionales",
                "content": "El Congreso de Colombia inició el debate...",
                "author": "Juan Pérez",
                "word_count": 850,
                "published_date": "2025-10-03T10:00:00Z",
                "scraped_at": "2025-10-03T12:00:00Z",
                "difficulty_score": 0.65,
                "tags": ["política", "congreso", "reforma"],
                "colombian_entities": ["Congreso", "Colombia"],
                "is_paywall": False
            }
        }
    )


class ScrapingStatusResponse(BaseModel):
    """Scraping status and statistics"""
    status: str
    total_articles: int
    recent_articles_24h: int
    last_scrape: Optional[datetime] = None
    source_distribution: List[Dict[str, Any]]
    available_scrapers: List[str]
    timestamp: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "operational",
                "total_articles": 15243,
                "recent_articles_24h": 342,
                "last_scrape": "2025-10-03T12:00:00Z",
                "source_distribution": [
                    {"source": "El Tiempo", "count": 5234},
                    {"source": "El Espectador", "count": 3421}
                ],
                "available_scrapers": ["El Tiempo", "El Espectador", "Semana"],
                "timestamp": "2025-10-03T12:30:00Z"
            }
        }
    )


class SourceConfigResponse(BaseModel):
    """Source configuration details"""
    name: str
    category: str
    url: HttpUrl
    priority: str
    scraping_enabled: bool
    last_scraped: Optional[datetime] = None
    total_articles: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "El Tiempo",
                "category": "media",
                "url": "https://www.eltiempo.com",
                "priority": "high",
                "scraping_enabled": True,
                "last_scraped": "2025-10-03T12:00:00Z",
                "total_articles": 5234
            }
        }
    )
