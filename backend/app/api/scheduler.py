"""
API endpoints for scheduler monitoring and management
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.scheduler import get_scheduler_service
from app.services.scheduler_jobs import (
    get_job_status, get_scheduler_metrics, trigger_manual_scrape
)

router = APIRouter()


@router.get("/status")
async def get_scheduler_status() -> Dict[str, Any]:
    """
    Get current scheduler status and statistics

    Returns comprehensive status including:
    - Running state
    - Active jobs count
    - Execution metrics
    - Uptime information
    """
    try:
        scheduler = get_scheduler_service()
        return scheduler.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching scheduler status: {str(e)}"
        )


@router.get("/jobs")
async def list_jobs() -> Dict[str, Any]:
    """
    List all active scheduler jobs with their configurations

    Returns:
    - Job ID and name
    - Next scheduled run time
    - Trigger configuration
    - Priority tier
    """
    try:
        scheduler = get_scheduler_service()
        status_data = scheduler.get_status()

        return {
            'total_jobs': status_data['total_jobs'],
            'jobs': status_data.get('jobs', []),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}")
async def get_job_details(job_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific job

    Args:
        job_id: Job identifier (e.g., 'scraper_el_tiempo')

    Returns:
    - Job configuration
    - Execution history
    - Success rate
    - Recent errors
    """
    try:
        scheduler = get_scheduler_service()

        # Get job configuration
        job_config = scheduler.get_job(job_id)
        if not job_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        # Get execution history
        job_status = get_job_status(job_id)

        return {
            'config': job_config,
            'status': job_status,
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching job details: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get scheduler performance metrics

    Returns:
    - Total executions
    - Success/failure rates
    - Jobs with issues
    - Performance statistics
    """
    try:
        metrics = get_scheduler_metrics()

        return {
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )


@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str) -> Dict[str, Any]:
    """
    Pause a scheduled job

    Args:
        job_id: Job identifier

    Returns:
    - Success status
    """
    try:
        scheduler = get_scheduler_service()
        success = scheduler.pause_job(job_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or could not be paused"
            )

        return {
            'success': True,
            'job_id': job_id,
            'status': 'paused',
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pausing job: {str(e)}"
        )


@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str) -> Dict[str, Any]:
    """
    Resume a paused job

    Args:
        job_id: Job identifier

    Returns:
    - Success status
    """
    try:
        scheduler = get_scheduler_service()
        success = scheduler.resume_job(job_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or could not be resumed"
            )

        return {
            'success': True,
            'job_id': job_id,
            'status': 'resumed',
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resuming job: {str(e)}"
        )


@router.post("/jobs/{job_id}/trigger")
async def trigger_job(job_id: str) -> Dict[str, Any]:
    """
    Manually trigger a job execution

    Args:
        job_id: Job identifier

    Returns:
    - Execution result
    """
    try:
        scheduler = get_scheduler_service()
        success = await scheduler.trigger_job(job_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or could not be triggered"
            )

        return {
            'success': True,
            'job_id': job_id,
            'status': 'triggered',
            'message': 'Job scheduled for immediate execution',
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering job: {str(e)}"
        )


@router.post("/scrape/{source_name}")
async def manual_scrape(source_name: str) -> Dict[str, Any]:
    """
    Manually trigger a scrape for a specific source

    Args:
        source_name: Name of source to scrape (e.g., 'El Tiempo')

    Returns:
    - Execution result with articles scraped
    """
    try:
        result = await trigger_manual_scrape(source_name)

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Scraping failed')
            )

        return {
            'success': True,
            'source': source_name,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing manual scrape: {str(e)}"
        )


@router.get("/health")
async def scheduler_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for scheduler

    Returns:
    - Scheduler health status
    - Recent failures
    - System availability
    """
    try:
        scheduler = get_scheduler_service()
        status_data = scheduler.get_status()
        metrics = get_scheduler_metrics()

        # Determine health status
        is_healthy = (
            status_data['running'] and
            metrics['jobs_with_issues'] < 5 and
            metrics['success_rate'] > 0.7
        )

        return {
            'status': 'healthy' if is_healthy else 'degraded',
            'running': status_data['running'],
            'active_jobs': status_data['total_jobs'],
            'success_rate': metrics['success_rate'],
            'jobs_with_issues': metrics['jobs_with_issues'],
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
