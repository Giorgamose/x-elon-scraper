# Quick Start Guide

Get the X Elon Scraper running in under 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- (Optional) X/Twitter API credentials

## Step 1: Clone & Configure

```bash
cd x-elon-scraper
cp .env.example .env
```

## Step 2: Add API Credentials (Optional but Recommended)

Edit `.env` and add your Twitter API credentials:

```bash
X_API_BEARER_TOKEN=your_bearer_token_here
X_API_KEY=your_api_key_here
# ... etc
```

**Don't have API credentials?** The system will automatically fall back to web scraping mode.

Get credentials at: https://developer.twitter.com/en/portal/dashboard

## Step 3: Start the System

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This starts:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Backend API (port 8000)
- Celery worker
- Celery beat scheduler
- React frontend (port 3000)

## Step 4: Access the Application

Open your browser:

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API**: http://localhost:8000

## Step 5: Collect Your First Posts

### Option A: Via Web UI

1. Go to http://localhost:3000
2. Click "Start Collection" button
3. Watch the dashboard update in real-time

### Option B: Via API

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_type": "collect_posts", "params": {"max_posts": 50}}'
```

### Option C: Via CLI

```bash
docker-compose exec backend python /app/../scripts/cli.py collect-now --max-posts 50
```

## Step 6: View Results

Browse collected posts at http://localhost:3000/posts

Or via API:
```bash
curl http://localhost:8000/api/v1/posts?limit=10
```

## Step 7: Check System Health

```bash
curl http://localhost:8000/health
```

Or via CLI:
```bash
docker-compose exec backend python /app/../scripts/cli.py health-check
```

## Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

### Stop the System

```bash
docker-compose -f docker-compose.dev.yml down
```

### Reset Database

```bash
docker-compose exec backend python /app/../scripts/cli.py rebuild-db
```

### Export Data

```bash
docker-compose exec backend python /app/../scripts/cli.py export-json --output /tmp/posts.json --limit 1000
```

### View Statistics

```bash
docker-compose exec backend python /app/../scripts/cli.py stats
```

## Troubleshooting

### "Database connection failed"

Check PostgreSQL is running:
```bash
docker-compose ps postgres
```

### "Worker not processing jobs"

Check Celery worker logs:
```bash
docker-compose logs worker
```

Ensure Redis is running:
```bash
docker-compose ps redis
```

### "Rate limit exceeded"

If using API mode: Wait 15 minutes for rate limit to reset.

If using scraper mode: Check `SCRAPER_RATE_LIMIT` in `.env` (increase delay).

### "Frontend can't connect to backend"

Check CORS settings in `.env`:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Ensure backend is running:
```bash
curl http://localhost:8000/health
```

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand system design
- See [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute
- Configure scheduled collection by editing `COLLECTION_CRON_*` in `.env`

## Production Deployment

For production use:

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Or use Makefile
make prod-up
```

Key differences:
- No hot reload
- Multiple worker replicas
- Stronger security (passwords required)
- Production-grade logging

## Support

- **Issues**: Open an issue on GitHub
- **Questions**: Check existing issues or documentation
- **Security**: Email security@example.com (never post credentials!)

---

Happy scraping! 🚀
