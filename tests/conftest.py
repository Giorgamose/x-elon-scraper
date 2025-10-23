"""Pytest configuration and fixtures."""
import asyncio
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db import Base
from app.models import job, post  # noqa: F401


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a test database with SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_post_data():
    """Sample post data for testing."""
    return {
        "id": "1234567890",
        "text": "This is a test tweet about Tesla and AI",
        "created_at": "2025-01-15T10:30:00.000Z",
        "author_id": "44196397",
        "public_metrics": {
            "retweet_count": 150,
            "reply_count": 45,
            "like_count": 1200,
            "quote_count": 30,
            "impression_count": 50000,
        },
        "lang": "en",
    }


@pytest.fixture
def sample_job_params():
    """Sample job parameters for testing."""
    return {
        "target_username": "elonmusk",
        "max_posts": 50,
    }
