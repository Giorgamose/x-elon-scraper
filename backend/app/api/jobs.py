"""API endpoints for job management."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import get_async_session
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    job_data: JobCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Create and start a new collection job.

    The job will be picked up by a Celery worker and executed asynchronously.
    Returns the created job with status='pending'.
    """
    try:
        # Create job
        job = Job(
            job_type=job_data.job_type,
            params=job_data.params or {},
            status=JobStatus.PENDING,
        )

        session.add(job)
        await session.commit()
        await session.refresh(job)

        logger.info(f"Created job {job.id} (type={job.job_type})")

        # Import here to avoid circular dependency
        from worker.tasks import execute_collection_job

        # Dispatch to Celery
        task = execute_collection_job.delay(job.id)
        job.celery_task_id = task.id

        await session.commit()
        await session.refresh(job)

        logger.info(f"Dispatched job {job.id} to Celery (task_id={task.id})")

        return JobResponse.model_validate(job)

    except Exception as e:
        logger.error(f"Error creating job: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List jobs with optional status filter.

    Returns jobs ordered by creation time (most recent first).
    """
    try:
        query = select(Job)

        # Apply status filter
        if status:
            query = query.where(Job.status == status)

        # Order by created_at descending
        query = query.order_by(desc(Job.created_at))

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        jobs = result.scalars().all()

        return [JobResponse.model_validate(job) for job in jobs]

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a specific job by ID.

    Returns 404 if job not found.
    """
    try:
        query = select(Job).where(Job.id == job_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return JobResponse.model_validate(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")


@router.delete("/{job_id}", status_code=204)
async def cancel_job(
    job_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Cancel a running or pending job.

    Returns 404 if job not found.
    Returns 400 if job is already in a terminal state.
    """
    try:
        query = select(Job).where(Job.id == job_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job.is_terminal:
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} is already {job.status}. Cannot cancel.",
            )

        # Cancel Celery task if exists
        if job.celery_task_id:
            from worker.celery_app import celery_app

            celery_app.control.revoke(job.celery_task_id, terminate=True)
            logger.info(f"Revoked Celery task {job.celery_task_id}")

        # Mark job as cancelled
        job.mark_cancelled()
        await session.commit()

        logger.info(f"Cancelled job {job_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling job: {str(e)}")
