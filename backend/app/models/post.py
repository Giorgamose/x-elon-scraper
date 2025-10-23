"""Post model for storing X/Twitter posts."""
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.config import settings
from app.db import Base, generate_uuid


class PostSource(str, Enum):
    """Source of the post data."""

    API = "api"
    SCRAPER = "scraper"


class Post(Base):
    """Model representing a post from X/Twitter."""

    __tablename__ = "posts"

    # Primary identification
    id = Column(String(36), primary_key=True, default=generate_uuid)
    post_id = Column(String(100), unique=True, nullable=False, index=True)

    # Author information
    author_username = Column(String(100), nullable=False, index=True)
    author_id = Column(String(100), nullable=True)
    author_name = Column(String(200), nullable=True)

    # Post content
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, index=True)
    collected_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())

    # Source and metadata
    source = Column(
        String(20),
        nullable=False,
        default=PostSource.API,
        index=True,
    )

    # Engagement metrics
    reply_count = Column(Integer, default=0)
    retweet_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    quote_count = Column(Integer, default=0)
    view_count = Column(Integer, nullable=True)

    # Relationship flags
    is_reply = Column(Boolean, default=False)
    is_retweet = Column(Boolean, default=False)
    is_quote = Column(Boolean, default=False)

    # Related post IDs
    replied_to_id = Column(String(100), nullable=True, index=True)
    retweeted_id = Column(String(100), nullable=True)
    quoted_id = Column(String(100), nullable=True)

    # Media attachments (array of URLs)
    media_urls = Column(
        JSONB if not settings.is_sqlite else JSON,
        nullable=True,
        default=list,
    )

    # Full raw data from API or scraper
    raw_data = Column(
        JSONB if not settings.is_sqlite else JSON,
        nullable=True,
    )

    # Content hash for deduplication
    content_hash = Column(String(64), nullable=True, index=True)

    # Soft delete flag
    is_deleted = Column(Boolean, default=False)

    # Indexes
    __table_args__ = (
        Index("ix_posts_created_at_desc", created_at.desc()),
        Index("ix_posts_source_created_at", source, created_at.desc()),
        Index("ix_posts_author_created_at", author_username, created_at.desc()),
        # Full-text search index (PostgreSQL specific)
        # Index("ix_posts_text_search", func.to_tsvector("english", text), postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Post(post_id={self.post_id}, author={self.author_username}, created_at={self.created_at})>"

    @property
    def has_media(self) -> bool:
        """Check if post has media attachments."""
        return bool(self.media_urls)

    @property
    def media_count(self) -> int:
        """Get number of media attachments."""
        return len(self.media_urls) if self.media_urls else 0

    def compute_content_hash(self) -> str:
        """Compute SHA-256 hash of post content for deduplication."""
        content = f"{self.post_id}:{self.text}:{self.created_at}"
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert post to dictionary."""
        return {
            "id": self.id,
            "post_id": self.post_id,
            "author_username": self.author_username,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "text": self.text,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "collected_at": (
                self.collected_at.isoformat() if self.collected_at else None
            ),
            "source": self.source,
            "reply_count": self.reply_count,
            "retweet_count": self.retweet_count,
            "like_count": self.like_count,
            "quote_count": self.quote_count,
            "view_count": self.view_count,
            "is_reply": self.is_reply,
            "is_retweet": self.is_retweet,
            "is_quote": self.is_quote,
            "replied_to_id": self.replied_to_id,
            "retweeted_id": self.retweeted_id,
            "quoted_id": self.quoted_id,
            "media_urls": self.media_urls or [],
            "has_media": self.has_media,
            "media_count": self.media_count,
            "is_deleted": self.is_deleted,
        }

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Post":
        """
        Create Post instance from X API v2 response.

        Expected format (simplified):
        {
            "id": "123456789",
            "text": "Tweet text",
            "created_at": "2025-01-01T00:00:00.000Z",
            "author_id": "44196397",
            "public_metrics": {
                "retweet_count": 10,
                "reply_count": 5,
                "like_count": 100,
                "quote_count": 2,
                "impression_count": 5000
            },
            "attachments": {
                "media_keys": ["3_123456"]
            },
            "referenced_tweets": [
                {"type": "replied_to", "id": "987654321"}
            ]
        }
        """
        metrics = data.get("public_metrics", {})
        attachments = data.get("attachments", {})
        referenced = data.get("referenced_tweets", [])

        # Parse referenced tweets
        is_reply = any(ref.get("type") == "replied_to" for ref in referenced)
        is_retweet = any(ref.get("type") == "retweeted" for ref in referenced)
        is_quote = any(ref.get("type") == "quoted" for ref in referenced)

        replied_to_id = None
        retweeted_id = None
        quoted_id = None

        for ref in referenced:
            ref_type = ref.get("type")
            ref_id = ref.get("id")
            if ref_type == "replied_to":
                replied_to_id = ref_id
            elif ref_type == "retweeted":
                retweeted_id = ref_id
            elif ref_type == "quoted":
                quoted_id = ref_id

        # Extract media URLs (need to be provided in includes.media)
        media_urls = []
        if "media" in data:
            for media in data["media"]:
                if "url" in media:
                    media_urls.append(media["url"])
                elif "preview_image_url" in media:
                    media_urls.append(media["preview_image_url"])

        # Parse created_at
        created_at_str = data.get("created_at")
        created_at = (
            datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if created_at_str
            else datetime.utcnow()
        )

        post = cls(
            post_id=data["id"],
            author_id=data.get("author_id"),
            text=data.get("text", ""),
            language=data.get("lang"),
            created_at=created_at,
            source=PostSource.API,
            reply_count=metrics.get("reply_count", 0),
            retweet_count=metrics.get("retweet_count", 0),
            like_count=metrics.get("like_count", 0),
            quote_count=metrics.get("quote_count", 0),
            view_count=metrics.get("impression_count"),
            is_reply=is_reply,
            is_retweet=is_retweet,
            is_quote=is_quote,
            replied_to_id=replied_to_id,
            retweeted_id=retweeted_id,
            quoted_id=quoted_id,
            media_urls=media_urls,
            raw_data=data,
        )

        post.content_hash = post.compute_content_hash()
        return post

    @classmethod
    def from_scraper_response(cls, data: Dict[str, Any]) -> "Post":
        """
        Create Post instance from web scraper response.

        Expected format:
        {
            "post_id": "123456789",
            "text": "Tweet text",
            "author_username": "elonmusk",
            "created_at": "2025-01-01T00:00:00",
            "reply_count": 5,
            "retweet_count": 10,
            "like_count": 100,
            "media_urls": ["https://..."],
            "is_reply": false,
            "replied_to_id": null
        }
        """
        created_at_str = data.get("created_at")
        created_at = (
            datetime.fromisoformat(created_at_str)
            if created_at_str
            else datetime.utcnow()
        )

        post = cls(
            post_id=data["post_id"],
            author_username=data.get("author_username", "unknown"),
            author_name=data.get("author_name"),
            text=data.get("text", ""),
            created_at=created_at,
            source=PostSource.SCRAPER,
            reply_count=data.get("reply_count", 0),
            retweet_count=data.get("retweet_count", 0),
            like_count=data.get("like_count", 0),
            quote_count=data.get("quote_count", 0),
            is_reply=data.get("is_reply", False),
            is_retweet=data.get("is_retweet", False),
            is_quote=data.get("is_quote", False),
            replied_to_id=data.get("replied_to_id"),
            retweeted_id=data.get("retweeted_id"),
            quoted_id=data.get("quoted_id"),
            media_urls=data.get("media_urls", []),
            raw_data=data,
        )

        post.content_hash = post.compute_content_hash()
        return post
