"""Export limits and quotas"""

from typing import Dict, Any
from enum import Enum


class ExportLimits:
    """Export limits and quotas configuration"""

    # Per-format limits
    MAX_ROWS = {
        'csv': 50000,
        'json': 100000,
        'jsonl': 1000000,
        'pdf': 100,
        'excel': 100000
    }

    # File size limits
    MAX_FILE_SIZE_MB = 50

    # User quotas
    MAX_EXPORTS_PER_HOUR = 10
    MAX_CONCURRENT_EXPORTS = 5

    # Processing limits
    CHUNK_SIZE = 1000  # Records to process at once
    MAX_PROCESSING_TIME_SECONDS = 300  # 5 minutes

    # Cleanup
    FILE_RETENTION_HOURS = 24

    @classmethod
    def get_format_limit(cls, format: str) -> int:
        """Get row limit for specific format"""
        return cls.MAX_ROWS.get(format.lower(), 10000)

    @classmethod
    def validate_export_size(cls, record_count: int, format: str) -> bool:
        """
        Validate if export size is within limits

        Args:
            record_count: Number of records to export
            format: Export format

        Returns:
            True if within limits
        """
        limit = cls.get_format_limit(format)
        return record_count <= limit

    @classmethod
    def get_estimated_time(cls, record_count: int, format: str) -> int:
        """
        Estimate export processing time in seconds

        Args:
            record_count: Number of records
            format: Export format

        Returns:
            Estimated time in seconds
        """
        # Base time estimates (seconds per 1000 records)
        time_per_1k = {
            'csv': 2,
            'json': 3,
            'jsonl': 2,
            'pdf': 10,  # PDF is slower
            'excel': 5
        }

        base_time = time_per_1k.get(format.lower(), 3)
        estimated = (record_count / 1000) * base_time

        return max(int(estimated), 1)  # Minimum 1 second
