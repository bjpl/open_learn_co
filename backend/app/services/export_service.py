"""Export service for managing data exports with async job processing"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pathlib import Path
import asyncio
import uuid
from enum import Enum

from .exporters import (
    BaseExporter,
    CSVExporter,
    JSONExporter,
    PDFExporter,
    ExcelExporter
)


class ExportStatus(str, Enum):
    """Export job status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Supported export formats"""
    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    PDF = "pdf"
    EXCEL = "excel"


class ExportJob:
    """Represents an export job"""

    def __init__(
        self,
        job_id: str,
        format: ExportFormat,
        record_count: int,
        filename: str
    ):
        self.job_id = job_id
        self.format = format
        self.record_count = record_count
        self.filename = filename
        self.status = ExportStatus.QUEUED
        self.progress = 0
        self.total = 100
        self.file_path: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None


class ExportService:
    """Service for managing data exports"""

    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Initialize exporters
        self.exporters: Dict[ExportFormat, BaseExporter] = {
            ExportFormat.CSV: CSVExporter(export_dir),
            ExportFormat.JSON: JSONExporter(export_dir),
            ExportFormat.JSONL: JSONExporter(export_dir),
            ExportFormat.PDF: PDFExporter(export_dir),
            ExportFormat.EXCEL: ExcelExporter(export_dir)
        }

        # Job tracking
        self.jobs: Dict[str, ExportJob] = {}
        self.max_concurrent_jobs = 5

        # Limits
        self.per_user_hourly_limit = 10
        self.max_file_size_mb = 50
        self.user_export_counts: Dict[str, List[datetime]] = {}

    async def create_export_job(
        self,
        data: List[Dict[str, Any]],
        format: ExportFormat,
        filename: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create and queue an export job

        Args:
            data: Data to export
            format: Export format
            filename: Base filename
            user_id: Optional user ID for rate limiting
            metadata: Optional metadata to include

        Returns:
            Job ID

        Raises:
            ValueError: If rate limit exceeded or invalid format
        """
        # Check rate limits
        if user_id:
            self._check_rate_limit(user_id)

        # Validate format
        if format not in self.exporters:
            raise ValueError(f"Unsupported export format: {format}")

        # Create job
        job_id = str(uuid.uuid4())
        job = ExportJob(
            job_id=job_id,
            format=format,
            record_count=len(data),
            filename=filename
        )

        self.jobs[job_id] = job

        # Process job asynchronously
        asyncio.create_task(self._process_export_job(job, data, metadata))

        # Track user export
        if user_id:
            if user_id not in self.user_export_counts:
                self.user_export_counts[user_id] = []
            self.user_export_counts[user_id].append(datetime.now())

        return job_id

    async def _process_export_job(
        self,
        job: ExportJob,
        data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]]
    ):
        """Process export job asynchronously"""
        try:
            job.status = ExportStatus.PROCESSING
            job.progress = 10

            # Get appropriate exporter
            exporter = self.exporters[job.format]

            # Update progress
            job.progress = 30

            # Export data based on format
            if job.format == ExportFormat.JSONL:
                file_path = await exporter.export_jsonl(data, job.filename, metadata)
            else:
                file_path = await exporter.export(data, job.filename, metadata)

            job.progress = 90

            # Verify file size
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                raise ValueError(f"Export file exceeds size limit: {file_size_mb:.2f} MB")

            job.progress = 100
            job.file_path = file_path
            job.status = ExportStatus.COMPLETED
            job.completed_at = datetime.now()

        except Exception as e:
            job.status = ExportStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of export job

        Args:
            job_id: Job ID

        Returns:
            Job status dict or None if not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return None

        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "total": job.total,
            "format": job.format.value,
            "record_count": job.record_count,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error,
            "file_ready": job.status == ExportStatus.COMPLETED
        }

    def get_file_path(self, job_id: str) -> Optional[str]:
        """
        Get file path for completed job

        Args:
            job_id: Job ID

        Returns:
            File path or None
        """
        job = self.jobs.get(job_id)
        if job and job.status == ExportStatus.COMPLETED:
            return job.file_path
        return None

    async def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old export files and jobs

        Args:
            max_age_hours: Maximum age of files to keep
        """
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        # Clean up files
        for exporter in self.exporters.values():
            await exporter.cleanup_old_files(max_age_hours)

        # Clean up job records
        expired_jobs = [
            job_id for job_id, job in self.jobs.items()
            if job.created_at.timestamp() < cutoff
        ]

        for job_id in expired_jobs:
            del self.jobs[job_id]

    def _check_rate_limit(self, user_id: str):
        """
        Check if user has exceeded rate limits

        Args:
            user_id: User ID

        Raises:
            ValueError: If rate limit exceeded
        """
        if user_id not in self.user_export_counts:
            return

        # Clean up old timestamps (older than 1 hour)
        cutoff = datetime.now().timestamp() - 3600
        self.user_export_counts[user_id] = [
            ts for ts in self.user_export_counts[user_id]
            if ts.timestamp() > cutoff
        ]

        # Check limit
        if len(self.user_export_counts[user_id]) >= self.per_user_hourly_limit:
            raise ValueError(
                f"Export rate limit exceeded. Maximum {self.per_user_hourly_limit} exports per hour."
            )

    async def export_articles(
        self,
        articles: List[Dict[str, Any]],
        format: ExportFormat,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export articles in specified format

        Args:
            articles: Article records
            format: Export format
            user_id: Optional user ID
            filters: Optional filters applied

        Returns:
            Job ID
        """
        metadata = {
            'type': 'articles',
            'filters_applied': filters or {}
        }

        return await self.create_export_job(
            data=articles,
            format=format,
            filename="articles",
            user_id=user_id,
            metadata=metadata
        )

    async def export_vocabulary(
        self,
        vocabulary: List[Dict[str, Any]],
        format: ExportFormat,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export vocabulary in specified format

        Args:
            vocabulary: Vocabulary records
            format: Export format
            user_id: Optional user ID
            filters: Optional filters applied

        Returns:
            Job ID
        """
        metadata = {
            'type': 'vocabulary',
            'filters_applied': filters or {}
        }

        return await self.create_export_job(
            data=vocabulary,
            format=format,
            filename="vocabulary",
            user_id=user_id,
            metadata=metadata
        )

    async def export_analysis(
        self,
        analysis_results: List[Dict[str, Any]],
        format: ExportFormat,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export analysis results in specified format

        Args:
            analysis_results: Analysis records
            format: Export format
            user_id: Optional user ID
            filters: Optional filters applied

        Returns:
            Job ID
        """
        metadata = {
            'type': 'analysis',
            'filters_applied': filters or {}
        }

        return await self.create_export_job(
            data=analysis_results,
            format=format,
            filename="analysis",
            user_id=user_id,
            metadata=metadata
        )


# Global export service instance
export_service = ExportService()
