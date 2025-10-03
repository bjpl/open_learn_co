"""
Pydantic validation schemas for OpenLearn Colombia API
Comprehensive input validation with security patterns
"""

from app.schemas.common_schemas import (
    PaginationParams,
    ErrorResponse,
    SuccessResponse,
    MessageResponse
)
from app.schemas.auth_schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    UserUpdate,
    PasswordReset,
    PasswordUpdate
)
from app.schemas.scraping_schemas import (
    ScrapingRequest,
    SourceFilter,
    ContentFilter,
    ScrapedContentResponse,
    ScrapingStatusResponse
)
from app.schemas.analysis_schemas import (
    AnalysisRequest,
    BatchAnalysisRequest,
    AnalysisResponse,
    AnalysisStatistics
)
from app.schemas.language_schemas import (
    VocabularyWordRequest,
    VocabularyWordResponse,
    PracticeSessionRequest,
    PracticeResultRequest,
    LearningProgressResponse
)

__all__ = [
    # Common
    "PaginationParams",
    "ErrorResponse",
    "SuccessResponse",
    "MessageResponse",
    # Auth
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "UserUpdate",
    "PasswordReset",
    "PasswordUpdate",
    # Scraping
    "ScrapingRequest",
    "SourceFilter",
    "ContentFilter",
    "ScrapedContentResponse",
    "ScrapingStatusResponse",
    # Analysis
    "AnalysisRequest",
    "BatchAnalysisRequest",
    "AnalysisResponse",
    "AnalysisStatistics",
    # Language
    "VocabularyWordRequest",
    "VocabularyWordResponse",
    "PracticeSessionRequest",
    "PracticeResultRequest",
    "LearningProgressResponse"
]
