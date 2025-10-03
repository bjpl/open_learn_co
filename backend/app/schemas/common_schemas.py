"""
Common validation schemas used across the application
Includes base models, pagination, and error handling
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters with validation (legacy - use OffsetPaginationParams)"""
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
        description="Maximum number of records to return"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skip": 0,
                "limit": 20
            }
        }
    )


class OffsetPaginationParams(BaseModel):
    """Offset-based pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset from page number"""
        return (self.page - 1) * self.limit

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "limit": 50
            }
        }
    )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters"""
    cursor: Optional[str] = Field(default=None, description="Pagination cursor token")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cursor": "eyJpZCI6MTIzLCJ2YWx1ZSI6IjIwMjUtMTAtMDNUMTI6MDA6MDAiLCJmaWVsZCI6InB1Ymxpc2hlZF9hdCJ9",
                "limit": 50
            }
        }
    )


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Has next page")
    has_prev: bool = Field(description="Has previous page")


class CursorPaginationMetadata(BaseModel):
    """Cursor pagination metadata"""
    next_cursor: Optional[str] = Field(default=None, description="Next page cursor")
    prev_cursor: Optional[str] = Field(default=None, description="Previous page cursor")
    has_more: bool = Field(description="Has more items")
    count: int = Field(description="Items in current page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T] = Field(description="Paginated items")
    total: int = Field(description="Total items")
    page: int = Field(description="Current page")
    pages: int = Field(description="Total pages")
    limit: int = Field(description="Items per page")

    model_config = ConfigDict(from_attributes=True)


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Generic cursor-paginated response"""
    items: List[T] = Field(description="Paginated items")
    next_cursor: Optional[str] = Field(default=None, description="Next cursor")
    has_more: bool = Field(description="Has more items")
    count: int = Field(description="Items in page")

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": {"field": "email", "reason": "Invalid format"},
                "timestamp": "2025-10-03T12:00:00Z"
            }
        }
    )


class SuccessResponse(BaseModel):
    """Standard success response format"""
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Response data"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": 123, "status": "active"},
                "timestamp": "2025-10-03T12:00:00Z"
            }
        }
    )


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str = Field(..., description="Response message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Operation completed"}
        }
    )


class DateRangeFilter(BaseModel):
    """Date range filter with validation"""
    start_date: Optional[datetime] = Field(
        default=None,
        description="Start date (ISO8601 format)"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="End date (ISO8601 format)"
    )

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_not_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure dates are not in the future"""
        if v and v > datetime.utcnow():
            raise ValueError("Date cannot be in the future")
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_after_start(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure end_date is after start_date"""
        start_date = info.data.get('start_date')
        if v and start_date and v < start_date:
            raise ValueError("end_date must be after start_date")
        return v


class SearchQuery(BaseModel):
    """Search query with sanitization"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query text"
    )

    @field_validator('query')
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Sanitize search query to prevent injection attacks"""
        # Remove SQL injection patterns
        dangerous_patterns = [
            '--', ';--', '/*', '*/', 'xp_', 'sp_', 'exec', 'execute',
            'union', 'select', 'insert', 'update', 'delete', 'drop',
            'create', 'alter', 'truncate'
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Query contains forbidden pattern: {pattern}")

        # Remove excessive whitespace
        v = ' '.join(v.split())

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"query": "Colombian politics analysis"}
        }
    )


class SortParams(BaseModel):
    """Sorting parameters"""
    sort_by: str = Field(
        default="created_at",
        description="Field to sort by"
    )
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: asc or desc"
    )

    @field_validator('sort_by')
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        """Validate sort field to prevent SQL injection"""
        # Only allow alphanumeric and underscore
        if not v.replace('_', '').isalnum():
            raise ValueError("Invalid sort field name")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }
    )
