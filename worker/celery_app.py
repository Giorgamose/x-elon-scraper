"""Celery application configuration."""
import sys
from pathlib import Path

from celery import Celery
from celery.schedules import crontab
from loguru import logger

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings

# Configure logging
logger.remove()
if settings.log_format == "json":
    logger.add(sys.stderr, format="{message}", level=settings.log_level, serialize=True)
else:
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level=settings.log_level,
    )

# Create Celery app
celery_app = Celery(
    "x_scraper_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["worker.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    result_expires=86400,  # Keep results for 24 hours
    broker_connection_retry_on_startup=True,
)

# Celery Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    "collect-posts-periodic": {
        "task": "worker.tasks.scheduled_collection",
        "schedule": crontab(
            minute=settings.collection_cron_minute,
            hour=settings.collection_cron_hour,
        ),
        "options": {"expires": 600},  # Expire if not executed within 10 minutes
    },
}

logger.info("Celery app configured")
logger.info(f"Broker: {settings.celery_broker_url}")
logger.info(f"Backend: {settings.celery_result_backend}")
logger.info(
    f"Schedule: {settings.collection_cron_minute} {settings.collection_cron_hour} * * *"
)
