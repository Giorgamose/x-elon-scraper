# X Elon Scraper - Architecture Documentation

## System Overview

The X Elon Scraper is a production-grade distributed system for collecting, storing, and analyzing posts from the public X (Twitter) account @elonmusk. The system follows a microservices-inspired architecture with clear separation of concerns.

## High-Level Architecture

```
┌─────────────┐
│   Frontend  │  React + Vite + Tailwind
│   (Port 3000)│  User interface
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│   Backend   │  FastAPI + SQLAlchemy
│   (Port 8000)│  REST API, business logic
└──────┬──────┘
       │
       ├─────────► PostgreSQL (Port 5432)
       │           Data persistence
       │
       └─────────► Redis (Port 6379)
                   Message broker + cache
                          ▲
                          │
                    ┌─────┴─────┐
                    │   Worker  │  Celery
                    │ Background│  Scraping jobs
                    └───────────┘
```

## Components

### 1. Backend API (FastAPI)

**Purpose**: REST API for data access and job management

**Responsibilities**:
- Expose REST endpoints for posts and jobs
- Handle authentication and validation
- Query database for post data
- Create and manage scraping jobs
- Provide health checks and metrics

**Key Files**:
- `backend/app/main.py` - Application entry point
- `backend/app/api/posts.py` - Post endpoints
- `backend/app/api/jobs.py` - Job endpoints
- `backend/app/models/` - SQLAlchemy models
- `backend/app/schemas/` - Pydantic request/response schemas

**Technology Stack**:
- FastAPI for async REST API
- SQLAlchemy 2.0 for ORM
- Pydantic for validation
- Uvicorn as ASGI server

### 2. Worker (Celery)

**Purpose**: Execute background scraping jobs

**Responsibilities**:
- Poll X API or scrape web pages
- Parse and normalize data
- Store posts in database
- Handle retries and failures
- Schedule periodic collection

**Key Files**:
- `worker/celery_app.py` - Celery configuration
- `worker/tasks.py` - Task definitions

**Technology Stack**:
- Celery for distributed task queue
- Redis as message broker
- Celery Beat for scheduling

### 3. Data Collection Layer

#### 3a. X API Client (`app/services/x_api_client.py`)

**Preferred collection method**

**Features**:
- OAuth 2.0 authentication
- Automatic rate limit handling
- Pagination support
- Retry logic with exponential backoff
- Incremental sync (fetch only new posts)

**Rate Limits**:
- Free tier: 300 requests / 15 minutes
- Each request fetches up to 100 tweets
- Automatic sleep when limit reached

#### 3b. Web Scraper (`app/services/scraper.py`)

**Fallback collection method**

**Features**:
- robots.txt compliance check
- Playwright headless browser
- Configurable rate limiting
- HTML parsing with BeautifulSoup
- Exponential backoff on errors

**Rate Limits**:
- Default: 0.5 requests/second (very conservative)
- Configurable via `SCRAPER_RATE_LIMIT`

### 4. Database (PostgreSQL)

**Schema**:

**Posts Table**:
```sql
CREATE TABLE posts (
    id VARCHAR(36) PRIMARY KEY,
    post_id VARCHAR(100) UNIQUE NOT NULL,
    author_username VARCHAR(100) NOT NULL,
    author_id VARCHAR(100),
    text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    collected_at TIMESTAMP NOT NULL,
    source VARCHAR(20) NOT NULL,  -- 'api' or 'scraper'
    like_count INTEGER DEFAULT 0,
    retweet_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    quote_count INTEGER DEFAULT 0,
    media_urls JSONB,
    raw_data JSONB,
    content_hash VARCHAR(64),
    is_deleted BOOLEAN DEFAULT FALSE,
    -- Indexes for performance
    INDEX idx_created_at_desc (created_at DESC),
    INDEX idx_source_created_at (source, created_at DESC)
);
```

**Jobs Table**:
```sql
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending, running, completed, failed
    params JSONB,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    posts_collected INTEGER DEFAULT 0,
    posts_failed INTEGER DEFAULT 0,
    celery_task_id VARCHAR(100),
    error_message TEXT
);
```

### 5. Frontend (React)

**Purpose**: Web UI for browsing and searching posts

**Pages**:
- **Dashboard**: Statistics, recent jobs, collection trigger
- **Posts**: List view with search and filters
- **Post Detail**: Full post view with media and metadata
- **Jobs**: Job management and monitoring

**Technology Stack**:
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Axios for API calls
- React Router for navigation

## Data Flow

### Collection Flow (API Mode)

1. **Trigger**: User clicks "Start Collection" or scheduled cron job fires
2. **Job Creation**: Backend creates Job record with status=pending
3. **Task Dispatch**: Backend sends task to Celery via Redis
4. **Worker Pickup**: Available worker picks up task
5. **API Fetch**: Worker calls X API client
6. **Rate Limiting**: Client respects X-Rate-Limit headers
7. **Pagination**: Client fetches all pages (up to max_posts)
8. **Parsing**: Convert API response to Post objects
9. **Deduplication**: Check if post_id already exists
10. **Storage**: Insert new posts into PostgreSQL
11. **Job Update**: Mark job as completed, update counters
12. **Frontend Poll**: Frontend refreshes job status

### Collection Flow (Scraper Mode)

1-4. Same as API mode
5. **Scraper Init**: Worker starts Playwright browser
6. **robots.txt Check**: Verify scraping is allowed
7. **Page Fetch**: Navigate to twitter.com/elonmusk
8. **Wait & Scroll**: Wait for tweets to load, scroll for more
9. **HTML Parse**: Extract tweet data from DOM
10-12. Same as API mode

### Query Flow

1. **User Request**: Frontend sends GET /api/v1/posts?limit=50
2. **Validation**: Pydantic validates query parameters
3. **Database Query**: SQLAlchemy builds SELECT query with filters
4. **Execution**: PostgreSQL executes query with indexes
5. **Serialization**: Convert Post objects to JSON
6. **Response**: Frontend receives and renders data

## Incremental Sync Strategy

**Problem**: Avoid re-collecting the same posts

**Solution**: ID-based tracking

1. Store `max_post_id` after each successful collection
2. Next collection uses `since_id=max_post_id` in API request
3. X API returns only tweets newer than `since_id`
4. No duplicates, no wasted API calls

**Implementation**:
```python
# Get last collected post ID
last_job = session.query(Job).filter(
    Job.status == JobStatus.COMPLETED
).order_by(Job.completed_at.desc()).first()

if last_job:
    latest_post = session.query(Post).order_by(
        Post.created_at.desc()
    ).first()
    since_id = latest_post.post_id

# Fetch only new tweets
tweets = client.get_user_tweets(
    username="elonmusk",
    since_id=since_id
)
```

## Error Handling

### Retry Strategy

**Transient Errors** (network issues, rate limits):
- Automatic retry with exponential backoff
- Tenacity library with configurable max attempts
- Wait: 2s → 4s → 8s → 16s...

**Permanent Errors** (auth failure, invalid data):
- No retry
- Log error with full traceback
- Mark job as failed
- Alert operator

### Circuit Breaker

For external services (X API), implement circuit breaker pattern:
- After N consecutive failures, open circuit
- Reject requests immediately (fail fast)
- Periodically test if service recovered
- Close circuit when healthy

## Scalability

### Horizontal Scaling

**Backend API**:
```bash
docker-compose up -d --scale backend=4
```
- Stateless design allows multiple replicas
- Load balancer distributes requests
- Each instance connects to shared PostgreSQL

**Workers**:
```bash
docker-compose up -d --scale worker=4
```
- Each worker processes different jobs
- Redis ensures no duplicate processing
- Increase concurrency for parallel scraping

**Database**:
- Use read replicas for query workload
- Write to primary, read from replicas
- Connection pooling (PgBouncer)

### Vertical Scaling

**Database**:
- Increase PostgreSQL shared_buffers
- Add more RAM for caching
- Faster SSD for IOPS

**Workers**:
- Increase `--concurrency` parameter
- More CPU cores = more parallel tasks

### Data Archival

For long-term storage:
1. **Hot Storage** (PostgreSQL): Last 6 months
2. **Warm Storage** (S3): 6-12 months
3. **Cold Storage** (Glacier): >12 months

Implement automatic archival:
```sql
-- Archive old posts
INSERT INTO posts_archive
SELECT * FROM posts
WHERE created_at < NOW() - INTERVAL '6 months';

DELETE FROM posts
WHERE created_at < NOW() - INTERVAL '6 months';
```

## Monitoring

### Metrics (Prometheus)

**Application Metrics**:
- `scraper_posts_collected_total{source="api"}` - Total posts collected
- `scraper_job_duration_seconds` - Job execution time
- `scraper_api_requests_total` - API request count
- `scraper_errors_total{type="rate_limit"}` - Error count by type

**System Metrics**:
- Database connection pool size
- Redis queue depth
- HTTP request latency (p50, p95, p99)
- Worker CPU/memory usage

### Logging

**Structured JSON Logs**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "worker.tasks",
  "message": "Job completed",
  "job_id": "abc-123",
  "posts_collected": 45,
  "duration_seconds": 12.5
}
```

**Log Aggregation**:
- Ship logs to ELK stack (Elasticsearch, Logstash, Kibana)
- Query: "Show all failed jobs in last 24h"
- Alert on error rate > 5%

### Alerting

**Critical Alerts** (page on-call):
- API down > 5 minutes
- Database connection failures
- Worker queue depth > 1000
- Error rate > 10%

**Warning Alerts** (email/Slack):
- Scraping blocked by robots.txt
- API rate limit frequently hit
- Disk usage > 80%
- Job success rate < 90%

## Security

### Secrets Management

**Never commit**:
- API keys, tokens, passwords
- `.env` files

**Use**:
- Environment variables
- HashiCorp Vault (production)
- AWS Secrets Manager
- Kubernetes Secrets

### API Security

**Implement**:
- Rate limiting per IP
- API key authentication
- CORS whitelist
- Input validation (Pydantic)
- SQL injection prevention (parameterized queries)

### Network Security

**Docker**:
- Private network for backend services
- Only expose frontend + API ports
- No direct database access from internet

**Production**:
- HTTPS/TLS for all external traffic
- VPC for cloud deployment
- Firewall rules
- Secrets encryption at rest

## Performance Optimization

### Database

**Indexes** (already implemented):
```sql
CREATE INDEX idx_posts_created_at_desc ON posts (created_at DESC);
CREATE INDEX idx_posts_source_created_at ON posts (source, created_at DESC);
CREATE INDEX idx_posts_text_search ON posts USING gin(to_tsvector('english', text));
```

**Query Optimization**:
- Use `EXPLAIN ANALYZE` to profile queries
- Add indexes for frequent WHERE clauses
- Use `LIMIT` for pagination
- Avoid `SELECT *`, specify columns

**Caching**:
- Redis for frequently accessed data
- Cache stats endpoint (TTL: 5 minutes)
- Cache post lists (TTL: 1 minute)
- Invalidate on new posts

### Frontend

**Optimization**:
- Code splitting (React.lazy)
- Image lazy loading
- Pagination (don't load all posts at once)
- Debounce search input
- Cache API responses (React Query)

## Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```
- Hot reload enabled
- Debug logging
- SQLite database (optional)

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```
- Multi-worker configuration
- Production logging
- PostgreSQL required
- Health checks enabled
- Restart policies

### Cloud Deployment

**AWS**:
- ECS/Fargate for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- ALB for load balancing
- CloudWatch for monitoring

**GCP**:
- Cloud Run for containers
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud Load Balancing

## Testing Strategy

**Unit Tests**:
- Test individual functions/classes
- Mock external dependencies
- Fast execution (<1s total)

**Integration Tests**:
- Test API endpoints
- Use in-memory SQLite
- Mock external APIs (tweepy)

**End-to-End Tests**:
- Full workflow testing
- Real database (test instance)
- Selenium for frontend

**Load Tests**:
- Apache JMeter / Locust
- Simulate 1000 concurrent users
- Measure throughput and latency

## Future Enhancements

1. **Real-time Updates**: WebSocket for live post streaming
2. **Sentiment Analysis**: NLP for tweet sentiment
3. **Media Download**: Store images/videos locally or S3
4. **Multi-User**: Support multiple Twitter accounts
5. **Analytics Dashboard**: Charts and visualizations
6. **Export Formats**: CSV, Parquet, Avro
7. **Webhook Integration**: Push new posts to external systems
8. **API v2**: GraphQL endpoint

---

**Architectural Decisions**:

- **Why FastAPI?** Async support, automatic OpenAPI docs, Pydantic validation
- **Why Celery?** Battle-tested, reliable, supports complex workflows
- **Why PostgreSQL?** ACID compliance, JSON support (JSONB), mature ecosystem
- **Why Redis?** Fast, simple, doubles as cache and message broker
- **Why React?** Component reusability, large ecosystem, TypeScript support

For questions or suggestions, open an issue on GitHub.
