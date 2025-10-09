"""Export API endpoints for data export functionality"""

from fastapi import APIRouter, HTTPException, Query, Response, Depends
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path

from app.services.export_service import (
    export_service,
    ExportFormat,
    ExportStatus
)
from app.utils.export import ExportLimits
from app.core.security import get_current_active_user
from app.database.models import User


router = APIRouter()


class ExportRequest(BaseModel):
    """Export request model"""
    format: ExportFormat = Field(..., description="Export format")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters to apply")
    fields: Optional[List[str]] = Field(None, description="Specific fields to include")
    limit: Optional[int] = Field(None, description="Maximum records to export")


class ExportResponse(BaseModel):
    """Export response model"""
    job_id: str
    status: str
    estimated_time: int
    message: str


class ExportStatusResponse(BaseModel):
    """Export status response model"""
    job_id: str
    status: str
    progress: int
    total: int
    format: str
    record_count: int
    created_at: str
    completed_at: Optional[str]
    error: Optional[str]
    file_ready: bool


@router.post("/export/articles", response_model=ExportResponse)
async def export_articles(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Export articles in specified format

    - **format**: Export format (csv, json, jsonl, pdf, excel)
    - **filters**: Optional filters (category, date_range, sentiment, etc.)
    - **fields**: Optional list of fields to include
    - **limit**: Maximum number of records to export

    Returns job_id for tracking export progress
    """
    try:
        # Mock article data for demonstration
        # In production, this would query the database with filters
        articles = _get_mock_articles(request.filters, request.limit)

        # Validate export size
        if not ExportLimits.validate_export_size(len(articles), request.format.value):
            limit = ExportLimits.get_format_limit(request.format.value)
            raise HTTPException(
                status_code=400,
                detail=f"Export size exceeds limit. Maximum {limit} records for {request.format.value} format."
            )

        # Filter fields if specified
        if request.fields:
            articles = _filter_fields(articles, request.fields)

        # Create export job
        job_id = await export_service.export_articles(
            articles=articles,
            format=request.format,
            user_id=current_user.id,  # Get user_id from authenticated user
            filters=request.filters
        )

        # Estimate processing time
        estimated_time = ExportLimits.get_estimated_time(
            len(articles),
            request.format.value
        )

        return ExportResponse(
            job_id=job_id,
            status="queued",
            estimated_time=estimated_time,
            message=f"Export job created. Exporting {len(articles)} articles as {request.format.value}."
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/export/vocabulary", response_model=ExportResponse)
async def export_vocabulary(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Export vocabulary in specified format

    - **format**: Export format (csv, json, jsonl, pdf, excel)
    - **filters**: Optional filters (difficulty_level, part_of_speech, etc.)
    - **fields**: Optional list of fields to include
    - **limit**: Maximum number of records to export

    Returns job_id for tracking export progress
    """
    try:
        # Mock vocabulary data
        vocabulary = _get_mock_vocabulary(request.filters, request.limit)

        # Validate export size
        if not ExportLimits.validate_export_size(len(vocabulary), request.format.value):
            limit = ExportLimits.get_format_limit(request.format.value)
            raise HTTPException(
                status_code=400,
                detail=f"Export size exceeds limit. Maximum {limit} records for {request.format.value} format."
            )

        # Filter fields if specified
        if request.fields:
            vocabulary = _filter_fields(vocabulary, request.fields)

        # Create export job
        job_id = await export_service.export_vocabulary(
            vocabulary=vocabulary,
            format=request.format,
            user_id=current_user.id,  # Get user_id from authenticated user
            filters=request.filters
        )

        estimated_time = ExportLimits.get_estimated_time(
            len(vocabulary),
            request.format.value
        )

        return ExportResponse(
            job_id=job_id,
            status="queued",
            estimated_time=estimated_time,
            message=f"Export job created. Exporting {len(vocabulary)} vocabulary items as {request.format.value}."
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/export/analysis", response_model=ExportResponse)
async def export_analysis(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Export analysis results in specified format

    - **format**: Export format (csv, json, jsonl, pdf, excel)
    - **filters**: Optional filters (analysis_type, date_range, etc.)
    - **fields**: Optional list of fields to include
    - **limit**: Maximum number of records to export

    Returns job_id for tracking export progress
    """
    try:
        # Mock analysis data
        analysis_results = _get_mock_analysis(request.filters, request.limit)

        # Validate export size
        if not ExportLimits.validate_export_size(len(analysis_results), request.format.value):
            limit = ExportLimits.get_format_limit(request.format.value)
            raise HTTPException(
                status_code=400,
                detail=f"Export size exceeds limit. Maximum {limit} records for {request.format.value} format."
            )

        # Filter fields if specified
        if request.fields:
            analysis_results = _filter_fields(analysis_results, request.fields)

        # Create export job
        job_id = await export_service.export_analysis(
            analysis_results=analysis_results,
            format=request.format,
            user_id=current_user.id,  # Get user_id from authenticated user
            filters=request.filters
        )

        estimated_time = ExportLimits.get_estimated_time(
            len(analysis_results),
            request.format.value
        )

        return ExportResponse(
            job_id=job_id,
            status="queued",
            estimated_time=estimated_time,
            message=f"Export job created. Exporting {len(analysis_results)} analysis results as {request.format.value}."
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/export/custom", response_model=ExportResponse)
async def export_custom(
    request: ExportRequest,
    data: List[Dict[str, Any]],
    current_user: User = Depends(get_current_active_user)
):
    """
    Export custom data in specified format

    - **data**: List of records to export
    - **format**: Export format (csv, json, jsonl, pdf, excel)
    - **limit**: Maximum number of records to export

    Returns job_id for tracking export progress
    """
    try:
        # Limit data if specified
        if request.limit:
            data = data[:request.limit]

        # Validate export size
        if not ExportLimits.validate_export_size(len(data), request.format.value):
            limit = ExportLimits.get_format_limit(request.format.value)
            raise HTTPException(
                status_code=400,
                detail=f"Export size exceeds limit. Maximum {limit} records for {request.format.value} format."
            )

        # Filter fields if specified
        if request.fields:
            data = _filter_fields(data, request.fields)

        # Create export job
        job_id = await export_service.create_export_job(
            data=data,
            format=request.format,
            filename="custom_export",
            user_id=current_user.id,  # Get user_id from authenticated user
            metadata={"type": "custom"}
        )

        estimated_time = ExportLimits.get_estimated_time(
            len(data),
            request.format.value
        )

        return ExportResponse(
            job_id=job_id,
            status="queued",
            estimated_time=estimated_time,
            message=f"Export job created. Exporting {len(data)} records as {request.format.value}."
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/status/{job_id}", response_model=ExportStatusResponse)
async def get_export_status(job_id: str):
    """
    Get status of export job

    - **job_id**: Export job ID

    Returns current status, progress, and details
    """
    status = export_service.get_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Export job not found")

    return ExportStatusResponse(**status)


@router.get("/export/download/{job_id}")
async def download_export(job_id: str):
    """
    Download exported file

    - **job_id**: Export job ID

    Returns file if export is complete
    """
    # Get job status
    status = export_service.get_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Export job not found")

    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Export not ready. Current status: {status['status']}"
        )

    # Get file path
    file_path = export_service.get_file_path(job_id)

    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Export file not found")

    # Determine media type based on format
    media_types = {
        'csv': 'text/csv',
        'json': 'application/json',
        'jsonl': 'application/jsonl',
        'pdf': 'application/pdf',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }

    format = status['format']
    media_type = media_types.get(format, 'application/octet-stream')

    # Return file
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=Path(file_path).name
    )


# Helper functions for mock data
def _get_mock_articles(filters: Optional[Dict[str, Any]], limit: Optional[int]) -> List[Dict[str, Any]]:
    """Get mock article data"""
    from datetime import datetime

    articles = [
        {
            'id': i,
            'title': f'Article {i}',
            'summary': f'Summary of article {i}',
            'content': f'Content of article {i}',
            'source': 'El Tiempo' if i % 2 == 0 else 'El Espectador',
            'category': 'Politics' if i % 3 == 0 else 'Economy',
            'published_date': datetime.now().isoformat(),
            'sentiment_score': 0.5 + (i % 10) / 20,
            'difficulty_level': 'B1' if i % 2 == 0 else 'B2',
            'url': f'https://example.com/article-{i}'
        }
        for i in range(1, min(limit or 100, 100) + 1)
    ]

    return articles


def _get_mock_vocabulary(filters: Optional[Dict[str, Any]], limit: Optional[int]) -> List[Dict[str, Any]]:
    """Get mock vocabulary data"""
    vocabulary = [
        {
            'id': i,
            'lemma': f'palabra{i}',
            'definition': f'Definition {i}',
            'translations': ['word1', 'word2'],
            'difficulty_level': 'B1' if i % 2 == 0 else 'B2',
            'part_of_speech': 'noun' if i % 2 == 0 else 'verb',
            'example_sentences': [f'Example sentence {i}'],
            'frequency_rank': i * 100
        }
        for i in range(1, min(limit or 100, 100) + 1)
    ]

    return vocabulary


def _get_mock_analysis(filters: Optional[Dict[str, Any]], limit: Optional[int]) -> List[Dict[str, Any]]:
    """Get mock analysis data"""
    from datetime import datetime

    analysis_results = [
        {
            'id': i,
            'content_id': i,
            'analysis_type': 'sentiment' if i % 2 == 0 else 'entity',
            'sentiment_score': 0.5 + (i % 10) / 20,
            'entities': ['Entity1', 'Entity2'],
            'topics': ['Topic1', 'Topic2'],
            'difficulty': 'B1' if i % 2 == 0 else 'B2',
            'confidence_score': 0.8 + (i % 10) / 50,
            'created_at': datetime.now().isoformat()
        }
        for i in range(1, min(limit or 100, 100) + 1)
    ]

    return analysis_results


def _filter_fields(data: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
    """Filter records to only include specified fields"""
    return [
        {k: v for k, v in record.items() if k in fields}
        for record in data
    ]
