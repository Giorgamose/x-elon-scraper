"""Pydantic schemas for Post model."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class PostSource(str, Enum):
    """Source of the post data."""

    API = "api"
    SCRAPER = "scraper"


class PostCreate(BaseModel):
    """Schema for creating a new post."""

    post_id: str = Field(..., description="Unique X post ID")
    author_username: str = Field(..., description="Author's username")
    author_id: Optional[str] = Field(None, description="Author's user ID")
    author_name: Optional[str] = Field(None, description="Author's display name")
    text: str = Field(..., description="Post text content")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en')")
    created_at: datetime = Field(..., description="When the post was created")
    source: PostSource = Field(PostSource.API, description="Data source")
    reply_count: int = Field(0, ge=0, description="Number of replies")
    retweet_count: int = Field(0, ge=0, description="Number of retweets")
    like_count: int = Field(0, ge=0, description="Number of likes")
    quote_count: int = Field(0, ge=0, description="Number of quotes")
    view_count: Optional[int] = Field(None, ge=0, description="Number of views")
    is_reply: bool = Field(False, description="Is this a reply?")
    is_retweet: bool = Field(False, description="Is this a retweet?")
    is_quote: bool = Field(False, description="Is this a quote tweet?")
    replied_to_id: Optional[str] = Field(None, description="ID of replied-to post")
    retweeted_id: Optional[str] = Field(None, description="ID of retweeted post")
    quoted_id: Optional[str] = Field(None, description="ID of quoted post")
    media_urls: List[str] = Field(default_factory=list, description="Media URLs")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw API/scraper data")

    model_config = {"from_attributes": True}


class PostResponse(BaseModel):
    """Schema for post response."""

    id: str
    post_id: str
    author_username: str
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    text: str
    language: Optional[str] = None
    created_at: datetime
    collected_at: datetime
    source: PostSource
    reply_count: int
    retweet_count: int
    like_count: int
    quote_count: int
    view_count: Optional[int] = None
    is_reply: bool
    is_retweet: bool
    is_quote: bool
    replied_to_id: Optional[str] = None
    retweeted_id: Optional[str] = None
    quoted_id: Optional[str] = None
    media_urls: List[str]
    has_media: bool
    media_count: int
    is_deleted: bool

    model_config = {"from_attributes": True}


class PostSearchParams(BaseModel):
    """Schema for post search parameters."""

    q: Optional[str] = Field(None, description="Search query (text search)")
    source: Optional[PostSource] = Field(None, description="Filter by source")
    start_date: Optional[datetime] = Field(
        None, description="Filter posts after this date"
    )
    end_date: Optional[datetime] = Field(
        None, description="Filter posts before this date"
    )
    has_media: Optional[bool] = Field(None, description="Filter posts with media")
    is_reply: Optional[bool] = Field(None, description="Filter replies")
    is_retweet: Optional[bool] = Field(None, description="Filter retweets")
    is_quote: Optional[bool] = Field(None, description="Filter quote tweets")
    min_likes: Optional[int] = Field(None, ge=0, description="Minimum like count")
    min_retweets: Optional[int] = Field(None, ge=0, description="Minimum retweet count")
    limit: int = Field(50, ge=1, le=200, description="Number of results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc or desc)")

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort_by field."""
        allowed_fields = [
            "created_at",
            "collected_at",
            "like_count",
            "retweet_count",
            "reply_count",
        ]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {', '.join(allowed_fields)}")
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort_order field."""
        if v.lower() not in ("asc", "desc"):
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v.lower()


class PostStats(BaseModel):
    """Schema for post statistics."""

    total_posts: int
    posts_by_source: Dict[str, int]
    total_likes: int
    total_retweets: int
    total_replies: int
    avg_likes_per_post: float
    avg_retweets_per_post: float
    posts_with_media: int
    posts_with_media_percentage: float
    earliest_post: Optional[datetime] = None
    latest_post: Optional[datetime] = None
    posts_last_24h: int
    posts_last_7d: int
    posts_last_30d: int
