.PHONY: help install dev-up dev-down prod-up prod-down test lint format clean

help:
	@echo "X Elon Scraper - Available Commands"
	@echo ""
	@echo "  make install      - Install all dependencies"
	@echo "  make dev-up       - Start development environment"
	@echo "  make dev-down     - Stop development environment"
	@echo "  make prod-up      - Start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean generated files"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-make - Create new migration"

install:
	cd backend && pip install -r requirements.txt
	cd worker && pip install -r requirements.txt
	cd frontend && npm install

dev-up:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Services started. Access:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

dev-down:
	docker-compose -f docker-compose.dev.yml down

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

test:
	cd tests && pytest -v

test-cov:
	cd tests && pytest --cov=backend/app --cov-report=html --cov-report=term

lint:
	cd backend && flake8 app
	cd backend && mypy app

format:
	cd backend && black app
	cd backend && isort app

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

migrate:
	cd backend && alembic upgrade head

migrate-make:
	cd backend && alembic revision --autogenerate -m "$(message)"

logs:
	docker-compose -f docker-compose.dev.yml logs -f

shell:
	docker-compose -f docker-compose.dev.yml exec backend /bin/bash

db-shell:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U scraper -d x_scraper
