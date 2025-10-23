#!/usr/bin/env python
"""CLI tool for X Elon Scraper management tasks."""
import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import httpx
from loguru import logger
from sqlalchemy import func, select

from app.config import settings
from app.db import SyncSessionLocal, sync_engine, Base
from app.models.job import Job, JobStatus, JobType
from app.models.post import Post


def collect_now(max_posts: int = 100):
    """Trigger immediate collection job."""
    logger.info(f"Creating collection job for {max_posts} posts...")

    session = SyncSessionLocal()
    try:
        job = Job(
            job_type=JobType.COLLECT_POSTS,
            status=JobStatus.PENDING,
            params={"max_posts": max_posts, "manual": True},
        )

        session.add(job)
        session.commit()
        session.refresh(job)

        logger.info(f"✓ Job created: {job.id}")
        logger.info("Job will be picked up by a worker shortly.")

        return job.id

    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def rebuild_db():
    """Rebuild database schema (WARNING: destructive)."""
    response = input(
        "⚠️  WARNING: This will DROP all tables and rebuild the schema. "
        "All data will be lost. Continue? (yes/no): "
    )

    if response.lower() != "yes":
        logger.info("Cancelled.")
        return

    logger.info("Dropping all tables...")
    Base.metadata.drop_all(sync_engine)

    logger.info("Creating tables...")
    Base.metadata.create_all(sync_engine)

    logger.info("✓ Database rebuilt successfully.")


def export_json(output_file: str, start_date: str = None, limit: int = 1000):
    """Export posts to JSON file."""
    logger.info(f"Exporting posts to {output_file}...")

    session = SyncSessionLocal()
    try:
        query = select(Post).where(Post.is_deleted == False)

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.where(Post.created_at >= start_dt)
            except ValueError:
                logger.error(f"Invalid date format: {start_date}. Use ISO format (YYYY-MM-DD)")
                return

        query = query.order_by(Post.created_at.desc()).limit(limit)

        result = session.execute(query)
        posts = result.scalars().all()

        posts_data = [post.to_dict() for post in posts]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"✓ Exported {len(posts_data)} posts to {output_file}")

    except Exception as e:
        logger.error(f"Export failed: {e}")
    finally:
        session.close()


def show_stats():
    """Display collection statistics."""
    session = SyncSessionLocal()
    try:
        # Total posts
        total_posts = session.query(func.count(Post.id)).scalar()

        # Posts by source
        posts_by_source = (
            session.query(Post.source, func.count(Post.id))
            .group_by(Post.source)
            .all()
        )

        # Engagement metrics
        total_likes = session.query(func.sum(Post.like_count)).scalar() or 0
        total_retweets = session.query(func.sum(Post.retweet_count)).scalar() or 0

        # Date range
        earliest = session.query(func.min(Post.created_at)).scalar()
        latest = session.query(func.max(Post.created_at)).scalar()

        # Jobs
        total_jobs = session.query(func.count(Job.id)).scalar()
        completed_jobs = (
            session.query(func.count(Job.id))
            .filter(Job.status == JobStatus.COMPLETED)
            .scalar()
        )

        print("\n" + "=" * 60)
        print("X ELON SCRAPER - STATISTICS")
        print("=" * 60)
        print(f"\n📊 Posts:")
        print(f"  Total:          {total_posts:,}")
        for source, count in posts_by_source:
            print(f"    {source.upper():12} {count:,}")
        print(f"\n❤️  Engagement:")
        print(f"  Total Likes:    {int(total_likes):,}")
        print(f"  Total Retweets: {int(total_retweets):,}")
        if total_posts > 0:
            print(f"  Avg Likes/Post: {int(total_likes / total_posts):,}")
        print(f"\n📅 Date Range:")
        if earliest and latest:
            print(f"  Earliest:       {earliest.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Latest:         {latest.strftime('%Y-%m-%d %H:%M')}")
        print(f"\n🔧 Jobs:")
        print(f"  Total:          {total_jobs}")
        print(f"  Completed:      {completed_jobs}")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
    finally:
        session.close()


def health_check():
    """Check system health."""
    logger.info("Checking system health...")

    # Check database
    try:
        session = SyncSessionLocal()
        session.execute("SELECT 1")
        session.close()
        logger.info("✓ Database: OK")
        db_ok = True
    except Exception as e:
        logger.error(f"✗ Database: FAILED - {e}")
        db_ok = False

    # Check API
    try:
        response = httpx.get(f"http://localhost:{settings.api_port}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✓ API: OK")
            api_ok = True
        else:
            logger.error(f"✗ API: FAILED - Status {response.status_code}")
            api_ok = False
    except Exception as e:
        logger.error(f"✗ API: FAILED - {e}")
        api_ok = False

    # Check Redis
    try:
        import redis

        r = redis.from_url(settings.redis_url)
        r.ping()
        logger.info("✓ Redis: OK")
        redis_ok = True
    except Exception as e:
        logger.error(f"✗ Redis: FAILED - {e}")
        redis_ok = False

    if db_ok and api_ok and redis_ok:
        logger.info("\n🎉 All systems operational!")
        return 0
    else:
        logger.error("\n⚠️  Some systems are down. Check logs above.")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="X Elon Scraper CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # collect-now command
    collect_parser = subparsers.add_parser(
        "collect-now", help="Start immediate collection job"
    )
    collect_parser.add_argument(
        "--max-posts", type=int, default=100, help="Maximum posts to collect"
    )

    # rebuild-db command
    subparsers.add_parser("rebuild-db", help="Rebuild database schema (DESTRUCTIVE)")

    # export-json command
    export_parser = subparsers.add_parser("export-json", help="Export posts to JSON")
    export_parser.add_argument("--output", required=True, help="Output file path")
    export_parser.add_argument("--start-date", help="Start date (ISO format)")
    export_parser.add_argument(
        "--limit", type=int, default=1000, help="Maximum posts to export"
    )

    # stats command
    subparsers.add_parser("stats", help="Show collection statistics")

    # health-check command
    subparsers.add_parser("health-check", help="Check system health")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")

    # Execute command
    if args.command == "collect-now":
        collect_now(args.max_posts)
    elif args.command == "rebuild-db":
        rebuild_db()
    elif args.command == "export-json":
        export_json(args.output, args.start_date, args.limit)
    elif args.command == "stats":
        show_stats()
    elif args.command == "health-check":
        return health_check()

    return 0


if __name__ == "__main__":
    sys.exit(main())
