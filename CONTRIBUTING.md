# Contributing to X Elon Scraper

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd x-elon-scraper
   ```

2. **Copy environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start development environment**
   ```bash
   make dev-up
   ```

## Code Style

We use the following tools to maintain code quality:

- **black**: Code formatting (line length: 88)
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run all formatters and linters:
```bash
make format
make lint
```

## Testing

We maintain comprehensive test coverage:

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test
pytest tests/unit/test_models.py::TestPostModel::test_create_post
```

## Commit Guidelines

Follow conventional commit messages:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:
```
feat: add rate limiting to scraper
fix: handle missing media URLs in API response
docs: update README with new environment variables
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write tests for new functionality
   - Ensure all tests pass
   - Follow code style guidelines

3. **Run checks**
   ```bash
   make format
   make lint
   make test
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements**
   - All tests must pass
   - Code coverage should not decrease
   - Follow code style guidelines
   - Include descriptive PR title and description
   - Reference any related issues

## Adding New Features

### Backend (FastAPI)

1. **Models**: Add SQLAlchemy models in `backend/app/models/`
2. **Schemas**: Add Pydantic schemas in `backend/app/schemas/`
3. **API Routes**: Add endpoints in `backend/app/api/`
4. **Services**: Add business logic in `backend/app/services/`
5. **Tests**: Add tests in `tests/unit/` and `tests/integration/`

### Frontend (React)

1. **Components**: Add reusable components in `frontend/src/components/`
2. **Pages**: Add page components in `frontend/src/pages/`
3. **API Client**: Update API client in `frontend/src/api/client.ts`
4. **Styling**: Use Tailwind CSS classes

### Worker (Celery)

1. **Tasks**: Add Celery tasks in `worker/tasks.py`
2. **Tests**: Add tests in `tests/unit/`

## Database Migrations

When modifying database models:

1. **Generate migration**
   ```bash
   make migrate-make message="your migration description"
   ```

2. **Review the generated migration**
   ```bash
   # Check backend/alembic/versions/
   ```

3. **Apply migration**
   ```bash
   make migrate
   ```

## Debugging

### View logs
```bash
make logs

# Or for specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

### Access container shell
```bash
make shell

# Or specific service
docker-compose exec backend /bin/bash
docker-compose exec worker /bin/bash
```

### Access database
```bash
make db-shell
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions and classes
- Update API documentation (OpenAPI/Swagger is auto-generated)
- Add inline comments for complex logic

## Questions or Issues?

- Check existing issues: [GitHub Issues](link-to-issues)
- Open a new issue with detailed description
- Tag appropriately: `bug`, `feature`, `question`, etc.

Thank you for contributing!
