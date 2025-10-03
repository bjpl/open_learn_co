"""Base exporter class for all export formats"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from pathlib import Path


class BaseExporter(ABC):
    """Base class for all export formatters"""

    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def export(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export data to file

        Args:
            data: List of records to export
            filename: Base filename (without extension)
            metadata: Optional metadata to include in export

        Returns:
            Path to exported file
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this format"""
        pass

    def generate_filename(self, base: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate timestamped filename

        Args:
            base: Base filename (e.g., 'articles')
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Filename with timestamp and extension
        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y-%m-%d_%H%M%S")
        extension = self.get_file_extension()

        # Sanitize base filename
        safe_base = "".join(c for c in base if c.isalnum() or c in ('-', '_'))

        return f"{safe_base}_{timestamp_str}.{extension}"

    def get_file_path(self, filename: str) -> Path:
        """Get full file path in export directory"""
        return self.export_dir / filename

    async def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Remove export files older than max_age_hours

        Args:
            max_age_hours: Maximum age of files to keep (default 24 hours)
        """
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        for file_path in self.export_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                try:
                    file_path.unlink()
                except Exception:
                    pass  # Ignore errors during cleanup

    def chunk_data(self, data: List[Dict[str, Any]], chunk_size: int = 1000):
        """
        Split data into chunks for processing

        Args:
            data: Data to chunk
            chunk_size: Size of each chunk

        Yields:
            Chunks of data
        """
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    def sanitize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sanitize data for export (remove sensitive fields, clean values)

        Args:
            data: Data to sanitize

        Returns:
            Sanitized data
        """
        # Fields to exclude from exports
        sensitive_fields = {'password', 'token', 'api_key', 'secret'}

        sanitized = []
        for record in data:
            clean_record = {
                k: v for k, v in record.items()
                if k.lower() not in sensitive_fields
            }
            sanitized.append(clean_record)

        return sanitized
