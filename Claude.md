# Claude.md - AI Assistant Context for X Elon Scraper

This document provides essential context for AI assistants (like Claude) working on this codebase.

## Project Overview

**X Elon Scraper** is a production-grade distributed system for collecting, storing, and analyzing posts from the public X (Twitter) account @elonmusk. It's a full-stack application demonstrating professional software engineering practices.

**Core Purpose**: Collect and archive social media posts with dual collection methods (API + web scraping), background job processing, and modern web UI for browsing/searching.

## Architecture at a Glance

```
Frontend (React/TS) → Backend (FastAPI) → PostgreSQL
                           ↓
                      Redis → Workers (Celery)
```

**Key Components**:
1. **Backend**: FastAPI REST API (port 8000)
2. **Frontend**: React + Vite + Tailwind (port 3000)
3. **Workers**: Celery background jobs (Redis broker)
4. **Database**: PostgreSQL (port 5432) or SQLite (local dev)
5. **Cache/Queue**: Redis (port 6379)

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI | Async REST API with auto-docs |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Queue | Celery + Redis | Distributed background jobs |
| Database | PostgreSQL | Primary data store |
| Frontend | React 18 + TypeScript | User interface |
| Styling | Tailwind CSS | Utility-first CSS |
| Build | Vite | Fast frontend builds |
| Container | Docker + Compose | Deployment |
| Testing | Pytest | Unit & integration tests |

## Project Structure

```
x-elon-scraper/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Settings (env vars)
│   │   ├── db.py              # Database session management
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── post.py        # Post model
│   │   │   └── job.py         # Job model
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   │   ├── post.py        # Post schemas
│   │   │   └── job.py         # Job schemas
│   │   ├── api/               # API route handlers
│   │   │   ├── posts.py       # /api/v1/posts endpoints
│   │   │   └── jobs.py        # /api/v1/jobs endpoints
│   │   ├── services/          # Business logic layer
│   │   │   ├── x_api_client.py    # X API v2 client (preferred)
│   │   │   ├── scraper.py         # Web scraper (fallback)
│   │   │   └── post_parser.py     # Parse API/HTML to Post
│   │   └── utils/             # Helper utilities
│   ├── alembic/               # Database migrations
│   │   ├── versions/          # Migration scripts
│   │   └── env.py             # Alembic config
│   └── requirements.txt       # Python dependencies
│
├── worker/                     # Celery worker
│   ├── celery_app.py          # Celery configuration
│   ├── tasks.py               # Task definitions (collect_posts)
│   └── requirements.txt       # Worker dependencies
│
├── frontend/                   # React application
│   ├── src/
│   │   ├── pages/             # Page components
│   │   │   ├── Dashboard.tsx  # Main dashboard
│   │   │   ├── PostList.tsx   # Posts list with search
│   │   │   ├── PostDetail.tsx # Single post view
│   │   │   └── Jobs.tsx       # Job management
│   │   ├── components/        # Reusable components
│   │   ├── api/               # API client (Axios)
│   │   │   └── client.ts      # HTTP client setup
│   │   └── App.tsx            # Root component
│   ├── vite.config.ts         # Vite configuration
│   └── package.json           # Node dependencies
│
├── tests/                      # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── conftest.py            # Pytest fixtures
│
├── scripts/
│   └── cli.py                 # CLI tool for common tasks
│
├── docker-compose.dev.yml      # Development environment
├── docker-compose.prod.yml     # Production environment
├── .env.example                # Environment template
├── README.md                   # User-facing documentation
├── ARCHITECTURE.md             # Detailed architecture docs
├── PROJECT_SUMMARY.md          # Project summary
└── CONTRIBUTING.md             # Contribution guidelines
```

## Key Concepts

### 1. Dual Collection Modes

**API Mode (Preferred)**:
- Location: `backend/app/services/x_api_client.py`
- Uses official X API v2 with OAuth 2.0
- Automatic rate limit handling (300 req/15min for free tier)
- Returns complete metadata, media URLs
- Supports incremental sync via `since_id` parameter

**Scraper Mode (Fallback)**:
- Location: `backend/app/services/scraper.py`
- Uses Playwright headless browser + BeautifulSoup
- Checks robots.txt before scraping
- Conservative rate limiting (0.5 req/sec default)
- Used when API credentials unavailable

### 2. Database Models

**Post Model** (`backend/app/models/post.py`):
- Core fields: `id`, `post_id` (X's ID), `text`, `created_at`
- Metadata: `author_username`, `author_id`
- Engagement: `like_count`, `retweet_count`, `reply_count`, `quote_count`
- JSON fields: `media_urls` (array), `raw_data` (full API response)
- Tracking: `source` (api/scraper), `collected_at`, `content_hash`
- Indexes on: `created_at DESC`, `source + created_at`

**Job Model** (`backend/app/models/job.py`):
- Status tracking: `pending` → `running` → `completed`/`failed`
- Fields: `job_type`, `params` (JSON), `started_at`, `completed_at`
- Metrics: `posts_collected`, `posts_failed`
- Links to Celery: `celery_task_id`

### 3. Background Job Flow

1. **Trigger**: User clicks "Start Collection" or cron fires
2. **Job Created**: Backend creates Job record in DB (status=pending)
3. **Task Dispatched**: Backend sends task to Celery via Redis
4. **Worker Pickup**: Celery worker retrieves task from Redis queue
5. **Collection**: Worker calls X API or scraper
6. **Parsing**: Raw data → Post objects via `post_parser.py`
7. **Storage**: Insert/update posts in PostgreSQL
8. **Job Update**: Mark job as completed, update metrics
9. **Frontend Poll**: Frontend refreshes job status via API

Location: `worker/tasks.py` → `collect_posts_task()`

### 4. API Endpoints

**Posts** (`backend/app/api/posts.py`):
- `GET /api/v1/posts` - List posts (paginated, filterable)
- `GET /api/v1/posts/{post_id}` - Get single post
- `GET /api/v1/posts/search?q=query` - Full-text search
- `GET /api/v1/posts/stats` - Collection statistics

**Jobs** (`backend/app/api/jobs.py`):
- `POST /api/v1/jobs` - Start new collection job
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/{job_id}` - Get job status
- `DELETE /api/v1/jobs/{job_id}` - Cancel job

**System**:
- `GET /health` - Health check (DB, Redis connectivity)
- `GET /metrics` - Prometheus metrics
- `GET /docs` - OpenAPI Swagger UI

### 5. Configuration

All configuration via environment variables (`.env` file):

**Critical Variables**:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# X API Credentials (optional, enables API mode)
X_API_BEARER_TOKEN=your_token
X_API_KEY=your_key
X_API_KEY_SECRET=your_secret
X_API_ACCESS_TOKEN=your_access_token
X_API_ACCESS_TOKEN_SECRET=your_secret

# Redis
REDIS_URL=redis://localhost:6379/0

# Collection Settings
COLLECTION_CRON_MINUTE=*/15  # Run every 15 minutes
COLLECTION_CRON_HOUR=*
SCRAPER_RATE_LIMIT=2.0        # Seconds between requests

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

See `.env.example` for full list.

## Common Development Tasks

### Running Locally

**Full stack (Docker)**:
```bash
docker-compose -f docker-compose.dev.yml up
```

**Backend only**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Worker only**:
```bash
cd worker
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info  # Scheduler
```

**Frontend only**:
```bash
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
cd backend

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Testing

```bash
cd tests

# Run all tests
pytest

# Run with coverage
pytest --cov=backend/app --cov-report=html

# Run specific test file
pytest unit/test_api_client.py

# Run with verbose output
pytest -v -s
```

### CLI Tool

```bash
cd scripts

# Trigger collection now
python cli.py collect-now --max-posts 100

# Export posts to JSON
python cli.py export-json --output posts.json

# View statistics
python cli.py stats

# Rebuild database (WARNING: destructive)
python cli.py rebuild-db
```

## Important Files to Check First

When investigating issues or adding features:

1. **Configuration**: `backend/app/config.py` - All settings
2. **Models**: `backend/app/models/` - Database schema
3. **API Routes**: `backend/app/api/` - Endpoint handlers
4. **Collection Logic**:
   - `backend/app/services/x_api_client.py` - API collection
   - `backend/app/services/scraper.py` - Web scraping
   - `worker/tasks.py` - Background job logic
5. **Frontend Pages**: `frontend/src/pages/` - UI components

## Common Issues & Solutions

### Issue: "Database connection failed"
**Check**:
- PostgreSQL running: `docker ps` (look for postgres container)
- Connection string correct in `.env`
- Migrations applied: `alembic upgrade head`

### Issue: "Worker not processing jobs"
**Check**:
- Redis running: `docker ps` (look for redis container)
- Worker running: `docker-compose logs worker`
- Celery broker URL correct in `.env`

### Issue: "Rate limit exceeded"
**Solution**:
- API mode: Wait 15 minutes, system auto-retries
- Scraper mode: Increase `SCRAPER_RATE_LIMIT` in `.env`

### Issue: "Frontend can't connect to backend"
**Check**:
- Backend running: `curl http://localhost:8000/health`
- CORS settings: Check `CORS_ORIGINS` in `.env`
- Browser console for error details

### Issue: "Scraper returns no posts"
**Check**:
- robots.txt allows scraping (automated check in code)
- X website structure unchanged (selectors may need update)
- Playwright installed: `playwright install chromium`

## Code Style & Standards

- **Python**: Black formatting, flake8 linting, mypy type checking
- **TypeScript**: Prettier formatting, ESLint
- **Type hints**: Required throughout Python code
- **Docstrings**: Google-style for all public functions
- **Imports**: Sorted with isort

Run quality checks:
```bash
# Python
cd backend
black .
flake8 .
mypy app/

# TypeScript
cd frontend
npm run lint
npm run format
```

## Security Considerations

- **Never commit**: `.env` files, API keys, passwords
- **Input validation**: All API inputs validated via Pydantic schemas
- **SQL injection**: Prevented via SQLAlchemy parameterized queries
- **CORS**: Whitelist specific origins, not `*`
- **Rate limiting**: Implemented for both API and scraping

## Performance Notes

- **Database indexes**: Already on `created_at`, `source`, consider adding more for frequent queries
- **Pagination**: Uses offset/limit (simple), consider cursor-based for large datasets
- **Caching**: Redis available but not yet implemented for queries
- **API calls**: Async with aiohttp for concurrent requests
- **Database pool**: Configured in `db.py`, adjust `pool_size` for load

## Monitoring & Debugging

**Logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail=100 backend
```

**Metrics**:
- Endpoint: `http://localhost:8000/metrics`
- Format: Prometheus text format
- Metrics: Request count, latency, active jobs, posts collected

**Health Check**:
```bash
curl http://localhost:8000/health
```

## Dependencies

**Backend** (see `backend/requirements.txt`):
- fastapi, uvicorn - Web framework
- sqlalchemy, alembic - ORM & migrations
- pydantic - Validation
- celery, redis - Background jobs
- tweepy - X API client
- playwright, beautifulsoup4 - Web scraping
- loguru - Logging
- prometheus-client - Metrics

**Frontend** (see `frontend/package.json`):
- react, react-dom, react-router-dom
- typescript
- vite
- tailwindcss
- axios

## Deployment

**Development**:
```bash
docker-compose -f docker-compose.dev.yml up
```
- Hot reload enabled
- Debug logging
- SQLite option

**Production**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```
- Optimized builds
- PostgreSQL required
- Health checks
- Restart policies

**Cloud Options**:
- AWS: ECS + RDS + ElastiCache
- GCP: Cloud Run + Cloud SQL + Memorystore
- Azure: Container Apps + PostgreSQL + Redis

## Testing Strategy

- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test API endpoints with in-memory SQLite
- **Mocking**: External services (X API) mocked with vcr or responses
- **Fixtures**: Shared test data in `tests/conftest.py`

## Future Enhancement Ideas

- [ ] Implement Redis caching for frequently accessed posts
- [ ] Add full-text search with PostgreSQL FTS indexes
- [ ] Support multiple Twitter accounts (multi-tenant)
- [ ] Real-time updates via WebSockets
- [ ] Sentiment analysis on post text
- [ ] Download and archive media files (images/videos)
- [ ] Export to more formats (CSV, Parquet, Avro)
- [ ] GraphQL API as alternative to REST

## Ethical & Legal

- **robots.txt**: Automated compliance check before scraping
- **Rate limiting**: Conservative defaults (0.5 req/sec for scraping)
- **Terms of Service**: Users responsible for compliance with X ToS
- **Data usage**: Educational/research purposes, not for resale
- **Attribution**: Always attribute content to original author

## Questions to Ask Before Changes

### Before Adding Features
- Does this fit the core purpose (post collection/archival)?
- Will this affect existing functionality?
- Are there security implications?
- How will this be tested?

### Before Changing Architecture
- Why change from current approach?
- What are the tradeoffs?
- Is it backward compatible?
- Will it require migration?

### Before Optimizing
- Have you measured the performance bottleneck?
- Is this a real user issue or premature optimization?
- What's the expected improvement?

## AI Assistant Guidelines

When working on this codebase:

1. **Read** relevant files before making changes
2. **Test** changes locally before committing
3. **Document** new features in README/ARCHITECTURE.md
4. **Follow** existing code style and patterns
5. **Consider** backward compatibility
6. **Ask** for clarification if requirements unclear
7. **Think** about production implications (scale, security, monitoring)

## Getting Help

- **Architecture**: See `ARCHITECTURE.md` for detailed system design
- **Setup**: See `README.md` for comprehensive setup guide
- **Contributing**: See `CONTRIBUTING.md` for guidelines
- **Quick Start**: See `QUICKSTART.md` for fast setup

---

**Last Updated**: 2025-10-23
**Version**: 1.0.0
**Maintainer**: Generated for AI assistant context
