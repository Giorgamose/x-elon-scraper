"""FastAPI application entry point."""
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from app.api import jobs, posts
from app.config import settings
from app.db import close_db, init_db

# Configure logging
logger.remove()
if settings.log_format == "json":
    logger.add(
        sys.stderr,
        format="{message}",
        level=settings.log_level,
        serialize=True,
    )
else:
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {'production' if settings.is_production else 'development'}")
    logger.info(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url}")
    logger.info(f"Using X API: {settings.should_use_api}")

    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(posts.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics" if settings.enable_metrics else None,
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns service health status and dependencies.
    """
    try:
        # Check database
        from app.db import async_engine

        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
            db_status = "connected"

        # Check Redis
        redis_status = "unknown"
        try:
            from redis import asyncio as aioredis

            redis = await aioredis.from_url(settings.redis_url)
            await redis.ping()
            redis_status = "connected"
            await redis.close()
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            redis_status = "disconnected"

        return {
            "status": "healthy",
            "version": settings.app_version,
            "database": db_status,
            "redis": redis_status,
            "api_mode": "api" if settings.should_use_api else "scraper",
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
            },
        )


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    if not settings.enable_metrics:
        return JSONResponse(
            status_code=404,
            content={"error": "Metrics disabled"},
        )

    from starlette.responses import Response

    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers if not settings.api_reload else 1,
        log_level=settings.log_level.lower(),
    )
