"""Application configuration management."""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # X/Twitter API Configuration
    x_api_bearer_token: Optional[str] = Field(default=None, alias="X_API_BEARER_TOKEN")
    x_api_key: Optional[str] = Field(default=None, alias="X_API_KEY")
    x_api_secret: Optional[str] = Field(default=None, alias="X_API_SECRET")
    x_api_access_token: Optional[str] = Field(default=None, alias="X_API_ACCESS_TOKEN")
    x_api_access_secret: Optional[str] = Field(
        default=None, alias="X_API_ACCESS_SECRET"
    )
    x_target_username: str = Field(default="elonmusk", alias="X_TARGET_USERNAME")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./x_scraper.db", alias="DATABASE_URL"
    )

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND"
    )

    # API Server Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")
    api_reload: bool = Field(default=False, alias="API_RELOAD")

    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Scraping Configuration
    use_api_first: bool = Field(default=True, alias="USE_API_FIRST")
    scraper_rate_limit: float = Field(default=0.5, alias="SCRAPER_RATE_LIMIT")
    scraper_max_retries: int = Field(default=3, alias="SCRAPER_MAX_RETRIES")
    scraper_backoff_factor: float = Field(default=2.0, alias="SCRAPER_BACKOFF_FACTOR")
    scraper_timeout: int = Field(default=30, alias="SCRAPER_TIMEOUT")
    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")

    # Job Scheduling
    collection_cron_minute: str = Field(default="*/15", alias="COLLECTION_CRON_MINUTE")
    collection_cron_hour: str = Field(default="*", alias="COLLECTION_CRON_HOUR")
    max_posts_per_job: int = Field(default=200, alias="MAX_POSTS_PER_JOB")

    # Logging & Monitoring
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")

    # Security
    secret_key: str = Field(
        default="change_this_to_a_random_secret_key_in_production", alias="SECRET_KEY"
    )

    # Storage Configuration
    media_storage_mode: str = Field(default="url_only", alias="MEDIA_STORAGE_MODE")
    media_storage_path: Optional[str] = Field(
        default=None, alias="MEDIA_STORAGE_PATH"
    )

    # Application Metadata
    app_name: str = "X Elon Scraper"
    app_version: str = "1.0.0"
    app_description: str = "Production-grade X/Twitter post collection system"

    @property
    def has_api_credentials(self) -> bool:
        """Check if X API credentials are configured."""
        return bool(self.x_api_bearer_token or (self.x_api_key and self.x_api_secret))

    @property
    def should_use_api(self) -> bool:
        """Determine if API mode should be used."""
        return self.use_api_first and self.has_api_credentials

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.database_url.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.api_reload and self.log_level != "DEBUG"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
