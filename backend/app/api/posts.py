"""API endpoints for posts."""
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import get_async_session
from app.models.post import Post, PostSource
from app.schemas.post import PostResponse, PostSearchParams, PostStats

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=List[PostResponse])
async def list_posts(
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    source: PostSource = Query(None, description="Filter by source"),
    has_media: bool = Query(None, description="Filter posts with media"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List posts with pagination and filters.

    Returns most recent posts first.
    """
    try:
        query = select(Post).where(Post.is_deleted == False)

        # Apply filters
        if source:
            query = query.where(Post.source == source)

        if has_media is not None:
            if has_media:
                query = query.where(Post.media_urls.isnot(None))
                query = query.where(func.json_array_length(Post.media_urls) > 0)
            else:
                query = query.where(
                    or_(
                        Post.media_urls.is_(None),
                        func.json_array_length(Post.media_urls) == 0,
                    )
                )

        # Order by created_at descending
        query = query.order_by(desc(Post.created_at))

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        posts = result.scalars().all()

        return [PostResponse.model_validate(post) for post in posts]

    except Exception as e:
        logger.error(f"Error listing posts: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching posts: {str(e)}")


@router.get("/search", response_model=List[PostResponse])
async def search_posts(
    params: PostSearchParams = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search posts with advanced filters.

    Supports full-text search, date ranges, engagement filters, etc.
    """
    try:
        query = select(Post).where(Post.is_deleted == False)

        # Text search (case-insensitive substring match)
        if params.q:
            query = query.where(Post.text.ilike(f"%{params.q}%"))

        # Source filter
        if params.source:
            query = query.where(Post.source == params.source)

        # Date range filters
        if params.start_date:
            query = query.where(Post.created_at >= params.start_date)

        if params.end_date:
            query = query.where(Post.created_at <= params.end_date)

        # Media filter
        if params.has_media is not None:
            if params.has_media:
                query = query.where(Post.media_urls.isnot(None))
                query = query.where(func.json_array_length(Post.media_urls) > 0)
            else:
                query = query.where(
                    or_(
                        Post.media_urls.is_(None),
                        func.json_array_length(Post.media_urls) == 0,
                    )
                )

        # Post type filters
        if params.is_reply is not None:
            query = query.where(Post.is_reply == params.is_reply)

        if params.is_retweet is not None:
            query = query.where(Post.is_retweet == params.is_retweet)

        if params.is_quote is not None:
            query = query.where(Post.is_quote == params.is_quote)

        # Engagement filters
        if params.min_likes is not None:
            query = query.where(Post.like_count >= params.min_likes)

        if params.min_retweets is not None:
            query = query.where(Post.retweet_count >= params.min_retweets)

        # Sorting
        sort_field = getattr(Post, params.sort_by)
        if params.sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)

        # Pagination
        query = query.limit(params.limit).offset(params.offset)

        result = await session.execute(query)
        posts = result.scalars().all()

        logger.info(
            f"Search query '{params.q}' returned {len(posts)} results "
            f"(limit={params.limit}, offset={params.offset})"
        )

        return [PostResponse.model_validate(post) for post in posts]

    except Exception as e:
        logger.error(f"Error searching posts: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a specific post by X post ID.

    Returns 404 if post not found.
    """
    try:
        query = select(Post).where(Post.post_id == post_id)
        result = await session.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

        return PostResponse.model_validate(post)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching post: {str(e)}")


@router.get("/stats/overview", response_model=PostStats)
async def get_post_stats(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get aggregate statistics about collected posts.

    Includes total counts, engagement metrics, and time-based breakdowns.
    """
    try:
        # Total posts
        total_posts_query = select(func.count(Post.id)).where(Post.is_deleted == False)
        total_posts_result = await session.execute(total_posts_query)
        total_posts = total_posts_result.scalar() or 0

        # Posts by source
        posts_by_source_query = (
            select(Post.source, func.count(Post.id))
            .where(Post.is_deleted == False)
            .group_by(Post.source)
        )
        posts_by_source_result = await session.execute(posts_by_source_query)
        posts_by_source = {row[0]: row[1] for row in posts_by_source_result.all()}

        # Engagement metrics
        metrics_query = select(
            func.sum(Post.like_count),
            func.sum(Post.retweet_count),
            func.sum(Post.reply_count),
            func.avg(Post.like_count),
            func.avg(Post.retweet_count),
        ).where(Post.is_deleted == False)
        metrics_result = await session.execute(metrics_query)
        metrics = metrics_result.one()

        total_likes = int(metrics[0] or 0)
        total_retweets = int(metrics[1] or 0)
        total_replies = int(metrics[2] or 0)
        avg_likes = float(metrics[3] or 0)
        avg_retweets = float(metrics[4] or 0)

        # Posts with media
        media_query = select(func.count(Post.id)).where(
            and_(
                Post.is_deleted == False,
                Post.media_urls.isnot(None),
                func.json_array_length(Post.media_urls) > 0,
            )
        )
        media_result = await session.execute(media_query)
        posts_with_media = media_result.scalar() or 0

        media_percentage = (
            (posts_with_media / total_posts * 100) if total_posts > 0 else 0
        )

        # Date range
        date_range_query = select(
            func.min(Post.created_at),
            func.max(Post.created_at),
        ).where(Post.is_deleted == False)
        date_range_result = await session.execute(date_range_query)
        date_range = date_range_result.one()

        earliest_post = date_range[0]
        latest_post = date_range[1]

        # Time-based counts
        now = datetime.utcnow()
        posts_last_24h_query = select(func.count(Post.id)).where(
            and_(
                Post.is_deleted == False,
                Post.created_at >= now - timedelta(hours=24),
            )
        )
        posts_last_24h_result = await session.execute(posts_last_24h_query)
        posts_last_24h = posts_last_24h_result.scalar() or 0

        posts_last_7d_query = select(func.count(Post.id)).where(
            and_(
                Post.is_deleted == False,
                Post.created_at >= now - timedelta(days=7),
            )
        )
        posts_last_7d_result = await session.execute(posts_last_7d_query)
        posts_last_7d = posts_last_7d_result.scalar() or 0

        posts_last_30d_query = select(func.count(Post.id)).where(
            and_(
                Post.is_deleted == False,
                Post.created_at >= now - timedelta(days=30),
            )
        )
        posts_last_30d_result = await session.execute(posts_last_30d_query)
        posts_last_30d = posts_last_30d_result.scalar() or 0

        return PostStats(
            total_posts=total_posts,
            posts_by_source=posts_by_source,
            total_likes=total_likes,
            total_retweets=total_retweets,
            total_replies=total_replies,
            avg_likes_per_post=round(avg_likes, 2),
            avg_retweets_per_post=round(avg_retweets, 2),
            posts_with_media=posts_with_media,
            posts_with_media_percentage=round(media_percentage, 2),
            earliest_post=earliest_post,
            latest_post=latest_post,
            posts_last_24h=posts_last_24h,
            posts_last_7d=posts_last_7d,
            posts_last_30d=posts_last_30d,
        )

    except Exception as e:
        logger.error(f"Error calculating post stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")
