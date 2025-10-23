"""Pydantic schemas for Job model."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of a scraping job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Type of scraping job."""

    COLLECT_POSTS = "collect_posts"
    BACKFILL = "backfill"
    UPDATE_METRICS = "update_metrics"


class JobCreate(BaseModel):
    """Schema for creating a new job."""

    job_type: JobType = Field(..., description="Type of job to execute")
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Job parameters"
    )

    model_config = {"from_attributes": True}


class JobUpdate(BaseModel):
    """Schema for updating a job."""

    status: Optional[JobStatus] = None
    error_message: Optional[str] = None
    posts_collected: Optional[int] = None
    posts_skipped: Optional[int] = None
    posts_failed: Optional[int] = None

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    """Schema for job response."""

    id: str
    job_type: str
    status: JobStatus
    params: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    posts_collected: int
    posts_skipped: int
    posts_failed: int
    error_message: Optional[str] = None
    retry_count: int
    celery_task_id: Optional[str] = None
    source_used: Optional[str] = None
    duration_seconds: Optional[float] = None
    success_rate: float
    metadata: Dict[str, Any]

    model_config = {"from_attributes": True}
