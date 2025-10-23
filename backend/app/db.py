"""Database configuration and session management."""
import uuid
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# SQLAlchemy Base
Base = declarative_base()


def _get_database_url() -> str:
    """Get database URL, converting sync SQLite URL to async if needed."""
    url = settings.database_url

    # For async operations with SQLite, use aiosqlite
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")

    # For PostgreSQL, ensure we use asyncpg
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")

    return url


def _get_sync_database_url() -> str:
    """Get synchronous database URL."""
    url = settings.database_url

    # Ensure we use psycopg2 for sync PostgreSQL
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://")

    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://")

    return url


# Async engine for async operations
async_engine = create_async_engine(
    _get_database_url(),
    echo=settings.log_level == "DEBUG",
    future=True,
    pool_pre_ping=True,
    poolclass=pool.NullPool if settings.is_sqlite else pool.QueuePool,
)

# Sync engine for migrations and CLI tools
sync_engine = create_engine(
    _get_sync_database_url(),
    echo=settings.log_level == "DEBUG",
    future=True,
    pool_pre_ping=True,
    poolclass=pool.NullPool if settings.is_sqlite else pool.QueuePool,
)

# Session factories
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

SyncSessionLocal = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Enable foreign keys for SQLite
@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite."""
    if settings.is_sqlite:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Generator[Session, None, None]:
    """Get synchronous database session for CLI and workers."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_db() -> None:
    """Initialize database (create tables if they don't exist)."""
    # Import models to register them with Base
    from app.models import job, post  # noqa: F401

    async with async_engine.begin() as conn:
        # In production, use Alembic migrations instead
        if settings.log_level == "DEBUG":
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())
