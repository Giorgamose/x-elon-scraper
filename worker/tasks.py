"""Celery tasks for X scraping and data collection."""
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from celery import Task
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.db import SyncSessionLocal
from app.models.job import Job, JobStatus
from app.models.post import Post
from worker.celery_app import celery_app


class DatabaseTask(Task):
    """Base task with database session management."""

    _session = None

    @property
    def session(self):
        """Get or create database session."""
        if self._session is None:
            self._session = SyncSessionLocal()
        return self._session

    def after_return(self, *args, **kwargs):
        """Close database session after task completion."""
        if self._session is not None:
            self._session.close()
            self._session = None


def collect_via_api(username: str, max_posts: int = 100, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Collect posts using X API.

    Args:
        username: Twitter username
        max_posts: Maximum number of posts to collect
        since_id: Collect posts after this ID

    Returns:
        List of post dicts from API
    """
    logger.info(f"Collecting via API: @{username} (max={max_posts}, since_id={since_id})")

    from app.services.x_api_client import get_api_client

    try:
        client = get_api_client()

        # Test connection
        if not client.test_connection():
            raise Exception("API connection test failed")

        # Fetch tweets
        tweets = client.get_recent_tweets(
            username=username,
            max_count=max_posts,
            since_id=since_id,
        )

        logger.info(f"API returned {len(tweets)} tweets")
        return tweets

    except Exception as e:
        logger.error(f"API collection failed: {e}")
        raise


async def collect_via_scraper(username: str, max_posts: int = 100) -> List[Dict[str, Any]]:
    """
    Collect posts using web scraping.

    Args:
        username: Twitter username
        max_posts: Maximum number of posts to collect

    Returns:
        List of post dicts from scraper
    """
    logger.info(f"Collecting via scraper: @{username} (max={max_posts})")

    from app.services.scraper import get_scraper

    try:
        scraper = await get_scraper()

        # Test scraper
        if not await scraper.test_scraping():
            raise Exception("Scraper test failed")

        # Scrape timeline
        posts = await scraper.scrape_user_timeline(
            username=username,
            max_posts=max_posts,
        )

        await scraper.close()

        logger.info(f"Scraper returned {len(posts)} posts")
        return posts

    except Exception as e:
        logger.error(f"Scraper collection failed: {e}")
        raise


@celery_app.task(base=DatabaseTask, bind=True, name="worker.tasks.execute_collection_job")
def execute_collection_job(self, job_id: str) -> Dict[str, Any]:
    """
    Execute a collection job.

    This task collects posts from X using either the API or scraper fallback,
    stores them in the database, and updates the job status.

    Args:
        job_id: ID of the job to execute

    Returns:
        Dict with job results
    """
    logger.info(f"Executing collection job {job_id}")

    session = self.session

    try:
        # Load job
        job = session.query(Job).filter(Job.id == job_id).one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Mark job as running
        job.mark_started()
        session.commit()

        # Extract parameters
        params = job.params or {}
        target_username = params.get("target_username", settings.x_target_username)
        max_posts = params.get("max_posts", settings.max_posts_per_job)
        since_id = params.get("since_id")

        # Determine collection method
        use_api = settings.should_use_api
        collected_posts = []

        try:
            if use_api:
                logger.info("Using X API for collection")
                raw_posts = collect_via_api(target_username, max_posts, since_id)
                job.source_used = "api"

                # Convert to Post objects
                for raw_post in raw_posts:
                    try:
                        post = Post.from_api_response(raw_post)
                        post.author_username = target_username
                        collected_posts.append(post)
                    except Exception as e:
                        logger.error(f"Error parsing API post: {e}")
                        job.posts_failed += 1

            else:
                logger.info("Using scraper for collection")

                # Run async scraper in sync context
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                raw_posts = loop.run_until_complete(
                    collect_via_scraper(target_username, max_posts)
                )
                job.source_used = "scraper"

                # Convert to Post objects
                for raw_post in raw_posts:
                    try:
                        post = Post.from_scraper_response(raw_post)
                        collected_posts.append(post)
                    except Exception as e:
                        logger.error(f"Error parsing scraped post: {e}")
                        job.posts_failed += 1

        except Exception as e:
            logger.error(f"Collection failed: {e}")
            raise

        # Store posts in database
        logger.info(f"Storing {len(collected_posts)} posts in database")

        for post in collected_posts:
            try:
                # Check if post already exists
                existing = (
                    session.query(Post)
                    .filter(Post.post_id == post.post_id)
                    .one_or_none()
                )

                if existing:
                    logger.debug(f"Post {post.post_id} already exists, skipping")
                    job.posts_skipped += 1
                else:
                    session.add(post)
                    job.posts_collected += 1

            except IntegrityError as e:
                logger.warning(f"Duplicate post {post.post_id}: {e}")
                session.rollback()
                job.posts_skipped += 1

        # Commit posts
        session.commit()

        # Mark job as completed
        job.mark_completed()
        job.metadata = {
            "collected_at": datetime.utcnow().isoformat(),
            "target_username": target_username,
        }
        session.commit()

        logger.info(
            f"Job {job_id} completed: {job.posts_collected} collected, "
            f"{job.posts_skipped} skipped, {job.posts_failed} failed"
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "posts_collected": job.posts_collected,
            "posts_skipped": job.posts_skipped,
            "posts_failed": job.posts_failed,
            "source_used": job.source_used,
        }

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        tb = traceback.format_exc()

        # Mark job as failed
        try:
            job = session.query(Job).filter(Job.id == job_id).one_or_none()
            if job:
                job.mark_failed(str(e), tb)
                session.commit()
        except Exception as commit_error:
            logger.error(f"Failed to update job status: {commit_error}")

        raise


@celery_app.task(name="worker.tasks.scheduled_collection")
def scheduled_collection() -> Dict[str, Any]:
    """
    Scheduled task to collect posts periodically.

    This task runs on a cron schedule (configured in celery_app.py)
    and creates a new collection job.

    Returns:
        Dict with job creation result
    """
    logger.info("Running scheduled collection")

    session = SyncSessionLocal()

    try:
        # Check for any running jobs
        running_jobs = (
            session.query(Job)
            .filter(Job.status == JobStatus.RUNNING)
            .filter(Job.job_type == "collect_posts")
            .count()
        )

        if running_jobs > 0:
            logger.warning(
                f"Skipping scheduled collection: {running_jobs} job(s) still running"
            )
            return {
                "status": "skipped",
                "reason": "job_already_running",
            }

        # Get last successful collection to determine since_id
        last_job = (
            session.query(Job)
            .filter(Job.status == JobStatus.COMPLETED)
            .filter(Job.job_type == "collect_posts")
            .order_by(Job.completed_at.desc())
            .first()
        )

        since_id = None
        if last_job and last_job.metadata:
            # Get max post_id from last collection
            latest_post = (
                session.query(Post)
                .filter(Post.collected_at >= last_job.started_at)
                .order_by(Post.created_at.desc())
                .first()
            )
            if latest_post:
                since_id = latest_post.post_id

        # Create new job
        job = Job(
            job_type="collect_posts",
            status=JobStatus.PENDING,
            params={
                "max_posts": settings.max_posts_per_job,
                "since_id": since_id,
                "scheduled": True,
            },
        )

        session.add(job)
        session.commit()
        session.refresh(job)

        logger.info(f"Created scheduled job {job.id} (since_id={since_id})")

        # Execute job
        task = execute_collection_job.delay(job.id)
        job.celery_task_id = task.id
        session.commit()

        return {
            "status": "started",
            "job_id": job.id,
            "celery_task_id": task.id,
        }

    except Exception as e:
        logger.error(f"Scheduled collection failed: {e}")
        raise

    finally:
        session.close()


@celery_app.task(name="worker.tasks.test_task")
def test_task(message: str = "Hello from Celery!") -> Dict[str, Any]:
    """
    Simple test task to verify Celery is working.

    Args:
        message: Test message

    Returns:
        Dict with test result
    """
    logger.info(f"Test task executed: {message}")
    return {
        "status": "success",
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
