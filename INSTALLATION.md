# Complete Installation Guide - X Elon Scraper

This guide provides detailed, step-by-step instructions for installing and running the X Elon Scraper locally on your machine.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
   - [Method 1: Docker (Recommended)](#method-1-docker-recommended)
   - [Method 2: Local Development (Manual)](#method-2-local-development-manual)
3. [Configuration](#configuration)
4. [Running the Application](#running-the-application)
5. [Verification](#verification)
6. [First Collection](#first-collection)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

---

## Prerequisites

### For Docker Method (Recommended)

**Required:**
- **Docker Desktop** (version 20.10+)
  - Windows: [Download Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - Mac: [Download Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
  - Linux: [Install Docker Engine](https://docs.docker.com/engine/install/)
- **Docker Compose** (usually included with Docker Desktop)
- **Git** for cloning the repository
- **Minimum 4GB RAM** available for Docker
- **10GB free disk space**

**Optional but Recommended:**
- X/Twitter API credentials (for API mode)
  - Get them at: https://developer.twitter.com/en/portal/dashboard
  - Without these, the system will use web scraping mode

### For Local Development Method

**Required:**
- **Python 3.11+** (3.11, 3.12 recommended)
  - Check: `python --version`
  - Download: https://www.python.org/downloads/
- **Node.js 18+** and npm
  - Check: `node --version` and `npm --version`
  - Download: https://nodejs.org/
- **PostgreSQL 14+**
  - Download: https://www.postgresql.org/download/
- **Redis 7+**
  - Windows: https://github.com/microsoftarchive/redis/releases
  - Mac: `brew install redis`
  - Linux: `sudo apt-get install redis-server`
- **Git**
- **8GB RAM** minimum
- **10GB free disk space**

**Optional:**
- **Make** (for using Makefile commands)
  - Windows: Install via Chocolatey (`choco install make`) or use Git Bash
  - Mac/Linux: Usually pre-installed

---

## Installation Methods

## Method 1: Docker (Recommended)

This is the easiest and fastest way to get the application running.

### Step 1: Install Docker

If you don't have Docker installed:

**Windows:**
1. Download [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Run the installer
3. Restart your computer if prompted
4. Open Docker Desktop and wait for it to start
5. Verify installation: Open PowerShell/CMD and run:
   ```powershell
   docker --version
   docker-compose --version
   ```

**Mac:**
1. Download [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Drag Docker to Applications folder
3. Open Docker from Applications
4. Verify installation in Terminal:
   ```bash
   docker --version
   docker-compose --version
   ```

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker-compose --version
```

### Step 2: Clone the Repository

```bash
# Navigate to where you want to store the project
cd ~/Documents  # or any directory you prefer

# Clone the repository
git clone https://github.com/Giorgamose/x-elon-scraper.git

# Navigate into the project directory
cd x-elon-scraper
```

### Step 3: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Now edit the `.env` file with your preferred text editor:

**Windows:**
```powershell
notepad .env
```

**Mac/Linux:**
```bash
nano .env
# or
vi .env
# or
code .env  # if you have VS Code
```

**Minimal Configuration (Web Scraping Mode):**

If you don't have X API credentials, the default `.env` values will work. Just verify these settings:

```bash
# Database (default for Docker)
DATABASE_URL=postgresql://scraper:scraper_password@postgres:5432/x_scraper

# Redis (default for Docker)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# CORS (default)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Target account
X_TARGET_USERNAME=elonmusk

# Scraping settings (conservative defaults)
SCRAPER_RATE_LIMIT=0.5
USE_API_FIRST=true
```

**Full Configuration (API Mode - Recommended):**

To use the X API (faster and more reliable), add your credentials:

1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a new Project and App
3. Generate API Keys and Tokens
4. Add them to `.env`:

```bash
# X API Credentials
X_API_BEARER_TOKEN=your_actual_bearer_token_here
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_API_ACCESS_TOKEN=your_access_token_here
X_API_ACCESS_SECRET=your_access_secret_here
```

### Step 4: Start the Application

```bash
# Start all services in detached mode (background)
docker-compose -f docker-compose.dev.yml up -d

# Or use the Makefile shortcut (if make is installed)
make dev-up
```

This command will:
1. Pull required Docker images (first time only, ~5-10 minutes)
2. Build custom images for backend, worker, and frontend
3. Start 6 containers:
   - PostgreSQL database
   - Redis cache/queue
   - FastAPI backend
   - Celery worker
   - Celery beat scheduler
   - React frontend

**Expected output:**
```
[+] Running 6/6
 ✔ Container x-scraper-postgres   Started
 ✔ Container x-scraper-redis      Started
 ✔ Container x-scraper-backend    Started
 ✔ Container x-scraper-worker     Started
 ✔ Container x-scraper-beat       Started
 ✔ Container x-scraper-frontend   Started
```

### Step 5: Wait for Services to Initialize

```bash
# Watch logs to see when services are ready
docker-compose -f docker-compose.dev.yml logs -f

# Or check specific service
docker-compose -f docker-compose.dev.yml logs -f backend
```

Wait until you see messages like:
- Backend: `Application startup complete`
- Worker: `celery@hostname ready`
- Frontend: `Local: http://localhost:3000/`

Press `Ctrl+C` to stop watching logs (services continue running).

### Step 6: Verify Installation

Check all containers are running:
```bash
docker-compose -f docker-compose.dev.yml ps
```

Expected output:
```
NAME                    STATUS    PORTS
x-scraper-backend       Up        0.0.0.0:8000->8000/tcp
x-scraper-beat          Up
x-scraper-frontend      Up        0.0.0.0:3000->3000/tcp
x-scraper-postgres      Up        0.0.0.0:5432->5432/tcp
x-scraper-redis         Up        0.0.0.0:6379->6379/tcp
x-scraper-worker        Up
```

**Access the application:**

Open your browser and navigate to:
- **Frontend UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

You should see the dashboard!

**🎉 Congratulations! Skip to [First Collection](#first-collection)**

---

## Method 2: Local Development (Manual)

This method gives you more control but requires more setup.

### Step 1: Install Prerequisites

#### Install Python 3.11+

**Windows:**
1. Download from https://www.python.org/downloads/
2. Run installer, check "Add Python to PATH"
3. Verify: `python --version`

**Mac:**
```bash
brew install python@3.11
python3 --version
```

**Linux:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 --version
```

#### Install Node.js 18+

**Windows/Mac:**
- Download from https://nodejs.org/
- Run installer
- Verify: `node --version` and `npm --version`

**Linux:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
npm --version
```

#### Install PostgreSQL

**Windows:**
1. Download from https://www.postgresql.org/download/windows/
2. Run installer (remember the password you set!)
3. Default port: 5432

**Mac:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Create Database:**
```bash
# Connect to PostgreSQL
sudo -u postgres psql  # Linux/Mac
# or open "SQL Shell (psql)" on Windows

# Create user and database
CREATE USER scraper WITH PASSWORD 'scraper_password';
CREATE DATABASE x_scraper OWNER scraper;
GRANT ALL PRIVILEGES ON DATABASE x_scraper TO scraper;
\q
```

#### Install Redis

**Windows:**
- Download from https://github.com/microsoftarchive/redis/releases
- Extract and run `redis-server.exe`

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Verify Redis:**
```bash
redis-cli ping
# Should return: PONG
```

### Step 2: Clone Repository

```bash
cd ~/Documents  # or your preferred directory
git clone https://github.com/Giorgamose/x-elon-scraper.git
cd x-elon-scraper
```

### Step 3: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` for local development:

```bash
# Database - local PostgreSQL
DATABASE_URL=postgresql://scraper:scraper_password@localhost:5432/x_scraper

# Redis - local
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true  # Enable hot reload for development

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000

# X API Credentials (optional)
X_API_BEARER_TOKEN=your_token_here
X_API_KEY=your_key_here
# ... etc

# Scraping
X_TARGET_USERNAME=elonmusk
SCRAPER_RATE_LIMIT=0.5
```

### Step 4: Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers (for web scraping)
playwright install chromium

# Run database migrations
alembic upgrade head

# Verify backend setup
python -c "from app.config import settings; print('Config loaded:', settings.DATABASE_URL)"
```

### Step 5: Set Up Worker

The worker uses the same Python environment as the backend.

```bash
cd ../worker  # from backend directory

# Copy/link to backend venv (if not already activated)
# Windows:
..\backend\venv\Scripts\activate
# Mac/Linux:
source ../backend/venv/bin/activate

# Install worker-specific dependencies (if any)
pip install -r requirements.txt
```

### Step 6: Set Up Frontend

```bash
cd ../frontend  # from worker directory

# Install Node.js dependencies
npm install

# Create frontend .env file
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

### Step 7: Start All Services

You'll need **4 separate terminal windows/tabs**:

**Terminal 1 - Backend API:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
cd worker
source ../backend/venv/bin/activate  # Windows: ..\backend\venv\Scripts\activate
celery -A celery_app worker --loglevel=info --concurrency=2
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
cd worker
source ../backend/venv/bin/activate  # Windows: ..\backend\venv\Scripts\activate
celery -A celery_app beat --loglevel=info
```

**Terminal 4 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 8: Verify Installation

Check each service:

1. **Backend**: http://localhost:8000/health
   - Should return: `{"status": "healthy", ...}`

2. **API Docs**: http://localhost:8000/docs
   - Should show Swagger UI

3. **Frontend**: http://localhost:3000
   - Should show the dashboard

4. **Database**:
   ```bash
   psql -U scraper -d x_scraper -h localhost
   \dt  # Should show tables: posts, jobs, alembic_version
   \q
   ```

5. **Redis**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

---

## Configuration

### Getting X/Twitter API Credentials

Using the official API is **highly recommended** for reliable data collection.

1. **Apply for Developer Account**:
   - Go to https://developer.twitter.com/en/portal/dashboard
   - Sign in with your Twitter account
   - Apply for a developer account (usually approved within 24 hours)

2. **Create a Project and App**:
   - Click "Create Project"
   - Name your project (e.g., "Elon Tweet Archiver")
   - Select "Use Case" → "Making a bot" or "Doing something else"
   - Click "Create App" within the project

3. **Generate Credentials**:
   - Go to your App's "Keys and Tokens" tab
   - Generate:
     - API Key and Secret
     - Bearer Token
     - Access Token and Secret
   - Copy all these values immediately (you can't see them again)

4. **Set Permissions**:
   - Go to "Settings" → "User authentication settings"
   - Enable OAuth 2.0
   - Set permissions: Read-only is sufficient
   - Add required scopes: `tweet.read`, `users.read`

5. **Add to `.env`**:
   ```bash
   X_API_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAALongTokenHere
   X_API_KEY=YourApiKeyHere
   X_API_SECRET=YourApiSecretHere
   X_API_ACCESS_TOKEN=YourAccessTokenHere
   X_API_ACCESS_SECRET=YourAccessSecretHere
   ```

6. **Restart Services** (if already running):
   ```bash
   # Docker:
   docker-compose -f docker-compose.dev.yml restart

   # Local: Restart backend and worker terminals (Ctrl+C, then re-run)
   ```

### Important Configuration Options

Edit `.env` to customize behavior:

```bash
# Collection frequency (cron format)
COLLECTION_CRON_MINUTE=*/15  # Every 15 minutes
COLLECTION_CRON_HOUR=*       # Every hour

# Maximum posts per job (safety limit)
MAX_POSTS_PER_JOB=200

# Rate limiting for scraper (seconds between requests)
SCRAPER_RATE_LIMIT=2.0  # Be conservative!

# Logging
LOG_LEVEL=INFO  # DEBUG for more details
LOG_FORMAT=json # or "text" for human-readable

# Target account
X_TARGET_USERNAME=elonmusk  # Change to any public account
```

---

## Running the Application

### Starting Services

**Docker (Recommended):**
```bash
# Start
docker-compose -f docker-compose.dev.yml up -d

# Stop
docker-compose -f docker-compose.dev.yml down

# Restart
docker-compose -f docker-compose.dev.yml restart

# Stop and remove volumes (DELETES DATA!)
docker-compose -f docker-compose.dev.yml down -v
```

**Local Development:**
```bash
# Start each service in a separate terminal (as shown in Step 7)

# Or use tmux/screen for session management:
tmux new-session -d -s backend 'cd backend && source venv/bin/activate && uvicorn app.main:app --reload'
tmux new-session -d -s worker 'cd worker && source ../backend/venv/bin/activate && celery -A celery_app worker --loglevel=info'
tmux new-session -d -s beat 'cd worker && source ../backend/venv/bin/activate && celery -A celery_app beat --loglevel=info'
tmux new-session -d -s frontend 'cd frontend && npm run dev'
```

### Viewing Logs

**Docker:**
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

**Local:**
- Logs appear in each terminal window where services are running
- Redirect to files:
  ```bash
  uvicorn app.main:app --reload 2>&1 | tee backend.log
  ```

---

## Verification

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0",
  "timestamp": "2025-01-15T12:00:00Z"
}
```

### Database Check

**Docker:**
```bash
docker-compose exec postgres psql -U scraper -d x_scraper

# Inside psql:
\dt                    # List tables
SELECT COUNT(*) FROM posts;  # Check posts
SELECT COUNT(*) FROM jobs;   # Check jobs
\q
```

**Local:**
```bash
psql -U scraper -d x_scraper -h localhost
# Same commands as above
```

### Redis Check

```bash
redis-cli ping
redis-cli INFO stats
```

### Check Running Services

**Docker:**
```bash
docker-compose ps

# Should show all containers "Up"
```

**Local:**
```bash
# Check ports are listening
netstat -an | grep LISTEN | grep -E '3000|8000|5432|6379'

# or
lsof -i :3000
lsof -i :8000
lsof -i :5432
lsof -i :6379
```

---

## First Collection

### Method A: Via Web UI (Easiest)

1. Open http://localhost:3000
2. You should see the Dashboard
3. Click the **"Start Collection"** button
4. Watch the job status update in real-time
5. Once completed, click **"Posts"** in the navigation
6. Browse collected tweets!

### Method B: Via API

```bash
# Start a collection job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "collect_posts",
    "params": {
      "max_posts": 50,
      "username": "elonmusk"
    }
  }'

# Response will include job_id
# {
#   "id": "abc-123-def",
#   "status": "pending",
#   ...
# }

# Check job status
curl http://localhost:8000/api/v1/jobs/abc-123-def

# List collected posts
curl http://localhost:8000/api/v1/posts?limit=10

# Search posts
curl http://localhost:8000/api/v1/posts/search?q=tesla&limit=10
```

### Method C: Via CLI Tool

**Docker:**
```bash
docker-compose exec backend python /app/../scripts/cli.py collect-now --max-posts 50
docker-compose exec backend python /app/../scripts/cli.py stats
```

**Local:**
```bash
cd scripts
python cli.py collect-now --max-posts 50
python cli.py stats
python cli.py health-check
```

### Expected First Collection Results

- **API Mode**: 50-100 posts in ~30-60 seconds
- **Scraper Mode**: 20-50 posts in ~2-5 minutes (slower due to rate limiting)

Check the **Jobs** page in the UI to see detailed status and metrics.

---

## Troubleshooting

### Issue: Docker containers won't start

**Check Docker is running:**
```bash
docker --version
docker ps
```

**Check Docker Desktop is running** (Windows/Mac)

**View container logs:**
```bash
docker-compose logs postgres
docker-compose logs redis
```

**Common fixes:**
```bash
# Remove old containers and volumes
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

### Issue: "Port already in use"

**Find what's using the port:**
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Mac/Linux
lsof -i :8000
lsof -i :3000
```

**Change ports in docker-compose.dev.yml:**
```yaml
backend:
  ports:
    - "8001:8000"  # Change 8000 to 8001

frontend:
  ports:
    - "3001:3000"  # Change 3000 to 3001
```

### Issue: "Database connection failed"

**Check PostgreSQL is running:**
```bash
# Docker
docker-compose ps postgres

# Local
pg_isready -U scraper -h localhost
```

**Check DATABASE_URL in .env:**
```bash
# For Docker, should be:
DATABASE_URL=postgresql://scraper:scraper_password@postgres:5432/x_scraper

# For local, should be:
DATABASE_URL=postgresql://scraper:scraper_password@localhost:5432/x_scraper
```

**Run migrations:**
```bash
# Docker
docker-compose exec backend alembic upgrade head

# Local
cd backend
alembic upgrade head
```

### Issue: "Redis connection failed"

**Check Redis is running:**
```bash
# Docker
docker-compose ps redis

# Local
redis-cli ping  # Should return "PONG"
```

**Check REDIS_URL in .env:**
```bash
# For Docker:
REDIS_URL=redis://redis:6379/0

# For local:
REDIS_URL=redis://localhost:6379/0
```

### Issue: "Worker not processing jobs"

**Check worker logs:**
```bash
# Docker
docker-compose logs worker

# Local
# Check the terminal where worker is running
```

**Verify Redis connection:**
```bash
redis-cli
> KEYS *
> QUIT
```

**Restart worker:**
```bash
# Docker
docker-compose restart worker beat

# Local
# Ctrl+C in worker/beat terminals, then restart commands
```

### Issue: "Frontend can't connect to backend"

**Check CORS settings in .env:**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Check backend is accessible:**
```bash
curl http://localhost:8000/health
```

**Check browser console** for error details (F12 → Console tab)

**For Docker, verify network:**
```bash
docker network ls
docker network inspect x-elon-scraper_default
```

### Issue: "Rate limit exceeded"

**API Mode:**
- Wait 15 minutes for limit to reset
- System will automatically retry
- Check limits: https://developer.twitter.com/en/docs/twitter-api/rate-limits

**Scraper Mode:**
- Increase delay in .env: `SCRAPER_RATE_LIMIT=3.0`
- Restart services

### Issue: "Playwright browser not found"

**Install browsers:**
```bash
# Docker (already included in image, but if needed)
docker-compose exec worker playwright install chromium

# Local
playwright install chromium
```

### Issue: Python/Node version mismatch

**Check versions:**
```bash
python --version  # Need 3.11+
node --version    # Need 18+
npm --version
```

**Use pyenv/nvm for version management:**
```bash
# Python version manager
pip install pyenv
pyenv install 3.11
pyenv local 3.11

# Node version manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

### Getting More Help

**Enable debug logging:**

Edit `.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart services and check logs for more details.

**Check system resources:**
```bash
# Docker
docker stats

# Local
top  # or htop
```

**Join community/report issues:**
- GitHub Issues: https://github.com/Giorgamose/x-elon-scraper/issues
- Check existing issues for solutions

---

## Next Steps

### Explore the Application

1. **Dashboard**: http://localhost:3000
   - View statistics
   - Start/monitor collection jobs
   - See recent activity

2. **Posts Page**: http://localhost:3000/posts
   - Browse collected posts
   - Search by keywords
   - Filter by date, source
   - Sort by engagement

3. **Jobs Page**: http://localhost:3000/jobs
   - View all collection jobs
   - Check job status and metrics
   - Cancel running jobs

4. **API Documentation**: http://localhost:8000/docs
   - Interactive API explorer
   - Test endpoints
   - View schemas

### Configure Scheduled Collection

Edit `.env` to run collections automatically:

```bash
# Collect every 30 minutes
COLLECTION_CRON_MINUTE=*/30
COLLECTION_CRON_HOUR=*

# Collect every hour
COLLECTION_CRON_MINUTE=0
COLLECTION_CRON_HOUR=*

# Collect daily at 9 AM
COLLECTION_CRON_MINUTE=0
COLLECTION_CRON_HOUR=9
```

Restart services to apply changes.

### Export Data

```bash
# Docker
docker-compose exec backend python /app/../scripts/cli.py export-json \
  --output /tmp/posts.json \
  --limit 1000

# Local
cd scripts
python cli.py export-json --output posts.json --limit 1000
```

### Read Documentation

- **Architecture**: See `ARCHITECTURE.md` for system design
- **API Reference**: See `README.md` for API details
- **Contributing**: See `CONTRIBUTING.md` to contribute
- **Quick Reference**: See `QUICKSTART.md` for common tasks

### Advanced Usage

**Scale workers:**
```bash
docker-compose up -d --scale worker=4
```

**Monitor metrics:**
```bash
curl http://localhost:8000/metrics
```

**Database backups:**
```bash
# Docker
docker-compose exec postgres pg_dump -U scraper x_scraper > backup.sql

# Restore
docker-compose exec -T postgres psql -U scraper x_scraper < backup.sql
```

**Production deployment:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Frequently Asked Questions

### Do I need X API credentials?

No, but **highly recommended**. Without API credentials, the system uses web scraping which is:
- Slower (2-5 minutes vs 30-60 seconds per job)
- Less reliable (website structure changes)
- More restrictive (conservative rate limiting)
- May violate X Terms of Service

### How much does X API access cost?

- **Free tier**: 300 requests per 15 minutes (sufficient for most use cases)
- **Basic**: $100/month (higher limits)
- **Pro**: $5,000/month (full access)

For personal archiving, free tier is usually enough.

### Can I collect posts from other accounts?

Yes! Edit `.env`:
```bash
X_TARGET_USERNAME=nasa  # or any public account
```

Or specify in API call:
```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_type": "collect_posts", "params": {"username": "nasa"}}'
```

### How do I stop the application?

**Docker:**
```bash
docker-compose -f docker-compose.dev.yml down
```

**Local:**
- Press `Ctrl+C` in each terminal window

### How do I update the application?

```bash
# Pull latest code
git pull origin main

# Docker - rebuild images
docker-compose down
docker-compose build
docker-compose up -d

# Local - update dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### Is this legal?

- **With API**: Yes, complies with X Terms of Service
- **Web Scraping**: Gray area, use at your own risk
- **Data usage**: Educational/research only, don't resell data
- **Always**: Attribute posts to original authors

See README.md "Legal & Ethical Considerations" section.

---

## Summary

**Quick Commands:**

```bash
# Docker Setup
git clone https://github.com/Giorgamose/x-elon-scraper.git
cd x-elon-scraper
cp .env.example .env
# Edit .env with your settings
docker-compose -f docker-compose.dev.yml up -d

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Health: http://localhost:8000/health

# Stop
docker-compose -f docker-compose.dev.yml down
```

**Need help?** Open an issue: https://github.com/Giorgamose/x-elon-scraper/issues

---

**Last Updated**: 2025-10-23
**Version**: 1.0.0
**Maintainer**: X Elon Scraper Team
