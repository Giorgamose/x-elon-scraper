"""Unit tests for database models."""
from datetime import datetime

import pytest

from app.models.job import Job, JobStatus, JobType
from app.models.post import Post, PostSource


class TestPostModel:
    """Tests for Post model."""

    def test_create_post_from_api_response(self, sample_post_data):
        """Test creating a Post from API response."""
        post = Post.from_api_response(sample_post_data)

        assert post.post_id == "1234567890"
        assert post.text == "This is a test tweet about Tesla and AI"
        assert post.source == PostSource.API
        assert post.like_count == 1200
        assert post.retweet_count == 150
        assert post.reply_count == 45
        assert post.language == "en"
        assert post.content_hash is not None

    def test_post_to_dict(self, sample_post_data):
        """Test converting Post to dictionary."""
        post = Post.from_api_response(sample_post_data)
        post.author_username = "elonmusk"

        post_dict = post.to_dict()

        assert post_dict["post_id"] == "1234567890"
        assert post_dict["author_username"] == "elonmusk"
        assert post_dict["like_count"] == 1200
        assert post_dict["source"] == "api"
        assert "created_at" in post_dict

    def test_post_has_media(self):
        """Test has_media property."""
        post = Post(
            post_id="123",
            text="Test",
            created_at=datetime.utcnow(),
            author_username="test",
        )

        assert not post.has_media
        assert post.media_count == 0

        post.media_urls = ["https://example.com/image1.jpg"]
        assert post.has_media
        assert post.media_count == 1

    def test_post_content_hash(self):
        """Test content hash computation."""
        post = Post(
            post_id="123",
            text="Test tweet",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            author_username="test",
        )

        hash1 = post.compute_content_hash()
        hash2 = post.compute_content_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest


class TestJobModel:
    """Tests for Job model."""

    def test_create_job(self, sample_job_params):
        """Test creating a Job."""
        job = Job(
            job_type=JobType.COLLECT_POSTS,
            params=sample_job_params,
            status=JobStatus.PENDING,
        )

        assert job.job_type == JobType.COLLECT_POSTS
        assert job.status == JobStatus.PENDING
        assert job.params["max_posts"] == 50
        assert job.posts_collected == 0

    def test_job_mark_started(self, sample_job_params):
        """Test marking job as started."""
        job = Job(
            job_type=JobType.COLLECT_POSTS,
            params=sample_job_params,
        )

        assert job.started_at is None
        job.mark_started()

        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    def test_job_mark_completed(self, sample_job_params):
        """Test marking job as completed."""
        job = Job(
            job_type=JobType.COLLECT_POSTS,
            params=sample_job_params,
        )
        job.mark_started()
        job.posts_collected = 50

        job.mark_completed()

        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.is_terminal

    def test_job_mark_failed(self, sample_job_params):
        """Test marking job as failed."""
        job = Job(
            job_type=JobType.COLLECT_POSTS,
            params=sample_job_params,
        )
        job.mark_started()

        job.mark_failed("Test error", "Test traceback")

        assert job.status == JobStatus.FAILED
        assert job.error_message == "Test error"
        assert job.error_traceback == "Test traceback"
        assert job.is_terminal

    def test_job_duration(self, sample_job_params):
        """Test job duration calculation."""
        job = Job(
            job_type=JobType.COLLECT_POSTS,
            params=sample_job_params,
        )

        assert job.duration_seconds is None

        job.mark_started()
        import time

        time.sleep(0.1)
        job.mark_completed()

        assert job.duration_seconds is not None
        assert job.duration_seconds > 0

    def test_job_success_rate(self, sample_job_params):
        """Test success rate calculation."""
        job = Job(
            job_type=JobType.COLLECT_POSTS,
            params=sample_job_params,
        )

        job.posts_collected = 80
        job.posts_failed = 20

        assert job.success_rate == 80.0

        job.posts_collected = 0
        job.posts_failed = 0
        assert job.success_rate == 0.0
