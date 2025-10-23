"""Job model for tracking scraping jobs."""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from app.config import settings
from app.db import Base, generate_uuid


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


class Job(Base):
    """Model representing a scraping/collection job."""

    __tablename__ = "jobs"

    # Primary identification
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_type = Column(String(50), nullable=False, index=True)

    # Status tracking
    status = Column(
        String(20),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
    )

    # Job parameters (e.g., max_posts, since_id, target_username)
    params = Column(
        JSONB if not settings.is_sqlite else JSON,
        nullable=True,
        default=dict,
    )

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Results
    posts_collected = Column(Integer, default=0)
    posts_skipped = Column(Integer, default=0)
    posts_failed = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Celery task ID for tracking
    celery_task_id = Column(String(100), nullable=True, index=True)

    # Metadata
    source_used = Column(String(20), nullable=True)  # "api" or "scraper"
    metadata = Column(
        JSONB if not settings.is_sqlite else JSON,
        nullable=True,
        default=dict,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate of post collection."""
        total = self.posts_collected + self.posts_failed
        if total == 0:
            return 0.0
        return (self.posts_collected / total) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "job_type": self.job_type,
            "status": self.status,
            "params": self.params or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "posts_collected": self.posts_collected,
            "posts_skipped": self.posts_skipped,
            "posts_failed": self.posts_failed,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "celery_task_id": self.celery_task_id,
            "source_used": self.source_used,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "metadata": self.metadata or {},
        }

    def mark_started(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error_message: str, traceback: Optional[str] = None) -> None:
        """Mark job as failed with error details."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_traceback = traceback

    def mark_cancelled(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
