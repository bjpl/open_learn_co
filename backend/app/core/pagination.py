"""
Core pagination utilities for API responses
Supports offset-based, cursor-based, and page-based pagination
"""

from typing import Generic, TypeVar, List, Optional, Dict, Any, Callable
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import base64
import json
from datetime import datetime
from urllib.parse import urlencode

T = TypeVar('T')


class PaginationConfig:
    """Global pagination configuration"""
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 100
    MIN_LIMIT = 1
    DEFAULT_PAGE_SIZE = 25


class OffsetPaginationParams(BaseModel):
    """Offset-based pagination parameters (traditional)"""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(
        default=PaginationConfig.DEFAULT_LIMIT,
        ge=PaginationConfig.MIN_LIMIT,
        le=PaginationConfig.MAX_LIMIT,
        description="Items per page"
    )

    @property
    def offset(self) -> int:
        """Calculate offset from page number"""
        return (self.page - 1) * self.limit

    @property
    def skip(self) -> int:
        """Alias for offset (SQLAlchemy compatibility)"""
        return self.offset


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters (for real-time data)"""
    cursor: Optional[str] = Field(default=None, description="Pagination cursor")
    limit: int = Field(
        default=PaginationConfig.DEFAULT_LIMIT,
        ge=PaginationConfig.MIN_LIMIT,
        le=PaginationConfig.MAX_LIMIT,
        description="Items per page"
    )
    direction: str = Field(default="next", pattern="^(next|prev)$")

    def decode_cursor(self) -> Optional[Dict[str, Any]]:
        """Decode cursor token"""
        if not self.cursor:
            return None

        try:
            decoded = base64.b64decode(self.cursor.encode()).decode()
            return json.loads(decoded)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return None


class PagePaginationParams(BaseModel):
    """Page-based pagination (simple)"""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(
        default=PaginationConfig.DEFAULT_PAGE_SIZE,
        ge=PaginationConfig.MIN_LIMIT,
        le=PaginationConfig.MAX_LIMIT,
        description="Items per page"
    )

    @property
    def offset(self) -> int:
        """Calculate offset"""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Alias for per_page"""
        return self.per_page


class PaginationMetadata(BaseModel):
    """Pagination metadata for responses"""
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
    """Generic paginated response wrapper"""
    items: List[T] = Field(description="Paginated items")
    metadata: PaginationMetadata = Field(description="Pagination metadata")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Generic cursor-paginated response wrapper"""
    items: List[T] = Field(description="Paginated items")
    metadata: CursorPaginationMetadata = Field(description="Cursor metadata")


def create_cursor(
    last_id: int,
    last_value: Any,
    sort_field: str = "id"
) -> str:
    """
    Create a cursor token from the last item

    Args:
        last_id: ID of the last item
        last_value: Value of the sort field for the last item
        sort_field: Field used for sorting

    Returns:
        Base64-encoded cursor token
    """
    cursor_data = {
        "id": last_id,
        "value": last_value if not isinstance(last_value, datetime) else last_value.isoformat(),
        "field": sort_field
    }
    cursor_json = json.dumps(cursor_data)
    return base64.b64encode(cursor_json.encode()).decode()


def parse_cursor(cursor: str) -> Optional[Dict[str, Any]]:
    """
    Parse and validate cursor token

    Args:
        cursor: Base64-encoded cursor token

    Returns:
        Decoded cursor data or None if invalid
    """
    try:
        decoded = base64.b64decode(cursor.encode()).decode()
        data = json.loads(decoded)

        # Validate cursor structure
        if not all(k in data for k in ["id", "value", "field"]):
            return None

        return data
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None


async def paginate_async(
    query: Select,
    db: AsyncSession,
    params: OffsetPaginationParams,
    count_query: Optional[Select] = None
) -> tuple[List[Any], PaginationMetadata]:
    """
    Apply offset-based pagination to async SQLAlchemy query

    Args:
        query: SQLAlchemy select statement
        db: Async database session
        params: Pagination parameters
        count_query: Optional custom count query (for optimization)

    Returns:
        Tuple of (items, metadata)
    """
    # Get total count
    if count_query is None:
        count_query = query.with_only_columns(func.count()).order_by(None)

    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Calculate pagination metadata
    pages = (total + params.limit - 1) // params.limit if total > 0 else 0
    has_next = params.page < pages
    has_prev = params.page > 1

    # Apply pagination to query
    paginated_query = query.limit(params.limit).offset(params.offset)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    metadata = PaginationMetadata(
        total=total,
        page=params.page,
        limit=params.limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )

    return items, metadata


def paginate_sync(
    query: Select,
    db: Session,
    params: OffsetPaginationParams,
    count_query: Optional[Select] = None
) -> tuple[List[Any], PaginationMetadata]:
    """
    Apply offset-based pagination to sync SQLAlchemy query

    Args:
        query: SQLAlchemy select statement
        db: Sync database session
        params: Pagination parameters
        count_query: Optional custom count query (for optimization)

    Returns:
        Tuple of (items, metadata)
    """
    # Get total count
    if count_query is None:
        count_query = query.with_only_columns(func.count()).order_by(None)

    total = db.execute(count_query).scalar() or 0

    # Calculate pagination metadata
    pages = (total + params.limit - 1) // params.limit if total > 0 else 0
    has_next = params.page < pages
    has_prev = params.page > 1

    # Apply pagination to query
    paginated_query = query.limit(params.limit).offset(params.offset)
    items = db.execute(paginated_query).scalars().all()

    metadata = PaginationMetadata(
        total=total,
        page=params.page,
        limit=params.limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )

    return items, metadata


async def paginate_cursor_async(
    query: Select,
    db: AsyncSession,
    params: CursorPaginationParams,
    sort_field: str = "id",
    sort_order: str = "desc"
) -> tuple[List[Any], CursorPaginationMetadata]:
    """
    Apply cursor-based pagination to async SQLAlchemy query

    Args:
        query: SQLAlchemy select statement
        db: Async database session
        params: Cursor pagination parameters
        sort_field: Field to sort by (default: id)
        sort_order: Sort direction (asc/desc)

    Returns:
        Tuple of (items, metadata)
    """
    # Parse cursor if provided
    cursor_data = params.decode_cursor() if params.cursor else None

    # Apply cursor filter
    if cursor_data:
        field_value = cursor_data.get("value")
        field_id = cursor_data.get("id")

        # Handle datetime conversion
        if isinstance(field_value, str):
            try:
                field_value = datetime.fromisoformat(field_value)
            except ValueError:
                pass

        # Apply cursor condition based on direction
        if sort_order.lower() == "desc":
            if params.direction == "next":
                # Get items before cursor (older)
                query = query.where(
                    (getattr(query.column_descriptions[0]['entity'], sort_field) < field_value) |
                    (
                        (getattr(query.column_descriptions[0]['entity'], sort_field) == field_value) &
                        (getattr(query.column_descriptions[0]['entity'], 'id') < field_id)
                    )
                )
            else:  # prev
                # Get items after cursor (newer)
                query = query.where(
                    (getattr(query.column_descriptions[0]['entity'], sort_field) > field_value) |
                    (
                        (getattr(query.column_descriptions[0]['entity'], sort_field) == field_value) &
                        (getattr(query.column_descriptions[0]['entity'], 'id') > field_id)
                    )
                )

    # Apply sorting
    sort_fn = desc if sort_order.lower() == "desc" else asc
    query = query.order_by(
        sort_fn(getattr(query.column_descriptions[0]['entity'], sort_field)),
        desc(getattr(query.column_descriptions[0]['entity'], 'id'))
    )

    # Fetch limit + 1 to check if there are more items
    paginated_query = query.limit(params.limit + 1)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    # Check if there are more items
    has_more = len(items) > params.limit
    if has_more:
        items = items[:params.limit]

    # Generate cursors
    next_cursor = None
    prev_cursor = None

    if items:
        last_item = items[-1]
        first_item = items[0]

        if has_more:
            next_cursor = create_cursor(
                last_item.id,
                getattr(last_item, sort_field),
                sort_field
            )

        # Always generate prev cursor if we have items
        if cursor_data:  # Not on first page
            prev_cursor = create_cursor(
                first_item.id,
                getattr(first_item, sort_field),
                sort_field
            )

    metadata = CursorPaginationMetadata(
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
        has_more=has_more,
        count=len(items)
    )

    return items, metadata


def create_pagination_links(
    base_url: str,
    params: Dict[str, Any],
    current_page: int,
    total_pages: int
) -> str:
    """
    Create RFC 5988 Link header for pagination

    Args:
        base_url: Base API URL
        params: Query parameters
        current_page: Current page number
        total_pages: Total number of pages

    Returns:
        Link header value
    """
    links = []

    # First page
    if current_page > 1:
        first_params = {**params, 'page': 1}
        links.append(f'<{base_url}?{urlencode(first_params)}>; rel="first"')

    # Previous page
    if current_page > 1:
        prev_params = {**params, 'page': current_page - 1}
        links.append(f'<{base_url}?{urlencode(prev_params)}>; rel="prev"')

    # Next page
    if current_page < total_pages:
        next_params = {**params, 'page': current_page + 1}
        links.append(f'<{base_url}?{urlencode(next_params)}>; rel="next"')

    # Last page
    if current_page < total_pages:
        last_params = {**params, 'page': total_pages}
        links.append(f'<{base_url}?{urlencode(last_params)}>; rel="last"')

    return ', '.join(links)


def estimate_count(
    db: Session,
    table_name: str,
    threshold: int = 10000
) -> int:
    """
    Get estimated row count for large tables (PostgreSQL specific)
    Falls back to exact count for small tables

    Args:
        db: Database session
        table_name: Name of the table
        threshold: Threshold for using estimation vs exact count

    Returns:
        Estimated or exact row count
    """
    # Try to get estimate from pg_class (PostgreSQL)
    try:
        result = db.execute(f"""
            SELECT reltuples::BIGINT AS estimate
            FROM pg_class
            WHERE relname = '{table_name}'
        """)
        estimate = result.scalar()

        if estimate and estimate < threshold:
            # Use exact count for small tables
            result = db.execute(f"SELECT COUNT(*) FROM {table_name}")
            return result.scalar()

        return int(estimate) if estimate else 0
    except Exception:
        # Fallback to exact count (works on all databases)
        result = db.execute(f"SELECT COUNT(*) FROM {table_name}")
        return result.scalar() or 0
