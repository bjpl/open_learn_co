"""
Pagination utility functions
"""

from typing import Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs
import base64
import json
from datetime import datetime


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
        Link header value following RFC 5988

    Example:
        <https://api.../articles?page=2&limit=50>; rel="next",
        <https://api.../articles?page=10>; rel="last"
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


def calculate_offset(page: int, limit: int) -> int:
    """
    Calculate offset from page number and limit

    Args:
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        Offset value for SQL query
    """
    if page < 1:
        page = 1
    return (page - 1) * limit


def calculate_total_pages(total_items: int, limit: int) -> int:
    """
    Calculate total number of pages

    Args:
        total_items: Total number of items
        limit: Items per page

    Returns:
        Total number of pages
    """
    if total_items == 0 or limit == 0:
        return 0
    return (total_items + limit - 1) // limit


def generate_cursor_token(
    last_id: int,
    last_value: Any,
    sort_field: str = "id"
) -> str:
    """
    Generate a cursor token from the last item

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
        "field": sort_field,
        "timestamp": datetime.utcnow().isoformat()
    }
    cursor_json = json.dumps(cursor_data)
    return base64.b64encode(cursor_json.encode()).decode()


def parse_cursor_token(cursor: str) -> Optional[Dict[str, Any]]:
    """
    Parse and validate cursor token

    Args:
        cursor: Base64-encoded cursor token

    Returns:
        Decoded cursor data or None if invalid
    """
    if not cursor:
        return None

    try:
        decoded = base64.b64decode(cursor.encode()).decode()
        data = json.loads(decoded)

        # Validate cursor structure
        required_fields = ["id", "value", "field"]
        if not all(k in data for k in required_fields):
            return None

        # Convert ISO datetime strings back to datetime objects
        if isinstance(data.get("value"), str):
            try:
                data["value"] = datetime.fromisoformat(data["value"])
            except (ValueError, TypeError):
                pass  # Keep as string if not a datetime

        return data
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def validate_pagination_params(
    page: Optional[int] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    max_limit: int = 100
) -> Dict[str, Any]:
    """
    Validate and normalize pagination parameters

    Args:
        page: Page number
        limit: Items per page
        cursor: Cursor token
        max_limit: Maximum allowed limit

    Returns:
        Validated parameters dict

    Raises:
        ValueError: If parameters are invalid
    """
    validated = {}

    if page is not None:
        if page < 1:
            raise ValueError("Page must be >= 1")
        validated["page"] = page

    if limit is not None:
        if limit < 1:
            raise ValueError("Limit must be >= 1")
        if limit > max_limit:
            raise ValueError(f"Limit must be <= {max_limit}")
        validated["limit"] = limit

    if cursor is not None:
        parsed = parse_cursor_token(cursor)
        if parsed is None:
            raise ValueError("Invalid cursor token")
        validated["cursor"] = cursor
        validated["cursor_data"] = parsed

    return validated


def create_pagination_metadata(
    total: int,
    page: int,
    limit: int
) -> Dict[str, Any]:
    """
    Create pagination metadata dictionary

    Args:
        total: Total number of items
        page: Current page number
        limit: Items per page

    Returns:
        Pagination metadata dict
    """
    pages = calculate_total_pages(total, limit)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }


def create_cursor_metadata(
    items: list,
    limit: int,
    sort_field: str = "id"
) -> Dict[str, Any]:
    """
    Create cursor pagination metadata

    Args:
        items: List of items (should be limit + 1 items)
        limit: Items per page
        sort_field: Field used for sorting

    Returns:
        Cursor metadata dict
    """
    has_more = len(items) > limit
    actual_items = items[:limit] if has_more else items

    next_cursor = None
    if has_more and actual_items:
        last_item = actual_items[-1]
        next_cursor = generate_cursor_token(
            getattr(last_item, 'id', 0),
            getattr(last_item, sort_field, None),
            sort_field
        )

    return {
        "next_cursor": next_cursor,
        "has_more": has_more,
        "count": len(actual_items)
    }


def extract_query_params(url: str) -> Dict[str, Any]:
    """
    Extract query parameters from URL

    Args:
        url: Full URL with query string

    Returns:
        Dictionary of query parameters
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Convert single-item lists to single values
    return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


def build_pagination_response(
    items: list,
    total: int,
    page: int,
    limit: int,
    base_url: Optional[str] = None,
    extra_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build complete pagination response with items and metadata

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        limit: Items per page
        base_url: Base URL for Link header (optional)
        extra_params: Additional query parameters (optional)

    Returns:
        Complete pagination response dict
    """
    metadata = create_pagination_metadata(total, page, limit)

    response = {
        "items": items,
        "total": metadata["total"],
        "page": metadata["page"],
        "pages": metadata["pages"],
        "limit": metadata["limit"]
    }

    # Add Link header if base_url provided
    if base_url:
        params = extra_params or {}
        params["limit"] = limit
        response["_links"] = create_pagination_links(
            base_url,
            params,
            page,
            metadata["pages"]
        )

    return response
