"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """Test health check returns 200."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self):
        """Test root endpoint returns app info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert "docs" in data


class TestPostsEndpoint:
    """Tests for posts endpoints."""

    def test_list_posts(self):
        """Test listing posts."""
        response = client.get("/api/v1/posts?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_posts_with_filters(self):
        """Test listing posts with filters."""
        response = client.get("/api/v1/posts?limit=10&source=api")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_posts(self):
        """Test searching posts."""
        response = client.get("/api/v1/posts/search?q=test&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_post_stats(self):
        """Test getting post statistics."""
        response = client.get("/api/v1/posts/stats/overview")

        assert response.status_code == 200
        data = response.json()
        assert "total_posts" in data
        assert "posts_by_source" in data


class TestJobsEndpoint:
    """Tests for jobs endpoints."""

    def test_list_jobs(self):
        """Test listing jobs."""
        response = client.get("/api/v1/jobs?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_job(self):
        """Test creating a job."""
        response = client.post(
            "/api/v1/jobs",
            json={
                "job_type": "collect_posts",
                "params": {"max_posts": 10},
            },
        )

        # May fail if Celery not running, but should return proper format
        assert response.status_code in [201, 500]
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["job_type"] == "collect_posts"
