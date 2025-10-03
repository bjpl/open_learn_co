"""Data sanitization utilities for exports"""

from typing import Any, Dict, List, Set, Optional
import re


# Sensitive field patterns to exclude
SENSITIVE_PATTERNS = {
    'password', 'token', 'api_key', 'secret', 'private_key',
    'access_token', 'refresh_token', 'auth_token', 'session_id',
    'credit_card', 'ssn', 'social_security'
}


def sanitize_for_export(
    data: List[Dict[str, Any]],
    exclude_fields: Optional[Set[str]] = None
) -> List[Dict[str, Any]]:
    """
    Sanitize data for export by removing sensitive fields

    Args:
        data: List of records to sanitize
        exclude_fields: Optional set of additional fields to exclude

    Returns:
        Sanitized data
    """
    if exclude_fields is None:
        exclude_fields = set()

    # Combine with default sensitive patterns
    all_sensitive = SENSITIVE_PATTERNS | exclude_fields

    sanitized = []
    for record in data:
        clean_record = {}

        for key, value in record.items():
            # Check if field name matches sensitive pattern
            if any(pattern in key.lower() for pattern in all_sensitive):
                continue

            # Sanitize value
            clean_value = sanitize_value(value)
            clean_record[key] = clean_value

        sanitized.append(clean_record)

    return sanitized


def sanitize_value(value: Any) -> Any:
    """
    Sanitize individual values

    Args:
        value: Value to sanitize

    Returns:
        Sanitized value
    """
    # Handle None
    if value is None:
        return None

    # Handle strings - remove potential injection attempts
    if isinstance(value, str):
        return sanitize_string(value)

    # Handle lists
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]

    # Handle dicts
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}

    # Return other types as-is
    return value


def sanitize_string(text: str) -> str:
    """
    Sanitize string values

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    # Remove potential CSV injection prefixes
    injection_prefixes = ['=', '+', '-', '@']
    if text and text[0] in injection_prefixes:
        text = "'" + text  # Prefix with single quote to prevent injection

    # Limit length for performance
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length] + '...'

    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal

    Args:
        filename: Filename to sanitize

    Returns:
        Safe filename
    """
    # Remove directory separators
    filename = filename.replace('/', '_').replace('\\', '_')

    # Keep only alphanumeric, dash, underscore, and dot
    filename = re.sub(r'[^a-zA-Z0-9\-_\.]', '_', filename)

    # Limit length
    if len(filename) > 200:
        # Keep extension
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            filename = parts[0][:190] + '.' + parts[1]
        else:
            filename = filename[:200]

    return filename


def redact_sensitive_text(text: str) -> str:
    """
    Redact sensitive information from text (emails, phone numbers, etc.)

    Args:
        text: Text to redact

    Returns:
        Redacted text
    """
    # Redact email addresses
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL_REDACTED]',
        text
    )

    # Redact phone numbers (various formats)
    text = re.sub(
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        '[PHONE_REDACTED]',
        text
    )

    # Redact URLs (optional - depends on use case)
    # text = re.sub(
    #     r'https?://[^\s]+',
    #     '[URL_REDACTED]',
    #     text
    # )

    return text
