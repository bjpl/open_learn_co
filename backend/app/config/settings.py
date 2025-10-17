"""
Application Settings and Configuration

Environment-specific configuration for:
- Application settings
- Database configuration
- Logging and monitoring
- External services
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # ========================================================================
    # Application Settings
    # ========================================================================

    APP_NAME: str = "OpenLearn API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: list[str] = ["*"]
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend base URL for email links

    # ========================================================================
    # Database Configuration
    # ========================================================================

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "openlearn"
    POSTGRES_PASSWORD: str = "openlearn123"
    POSTGRES_DB: str = "openlearn"

    @property
    def DATABASE_URL(self) -> str:
        """Async database URL for SQLAlchemy async operations"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous database URL for APScheduler and other sync operations"""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Database Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Elasticsearch
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX_PREFIX: str = "openlearn"
    ELASTICSEARCH_MAX_RESULT_WINDOW: int = 10000
    ELASTICSEARCH_TIMEOUT: int = 30  # seconds
    ELASTICSEARCH_MAX_RETRIES: int = 3

    @property
    def ELASTICSEARCH_URL(self) -> str:
        return f"http://{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"

    # Search Configuration
    SEARCH_DEFAULT_PAGE_SIZE: int = 10
    SEARCH_MAX_PAGE_SIZE: int = 100
    SEARCH_HIGHLIGHT_FRAGMENT_SIZE: int = 150
    SEARCH_AUTOCOMPLETE_MIN_LENGTH: int = 2
    SEARCH_AUTOCOMPLETE_MAX_SUGGESTIONS: int = 10

    # ========================================================================
    # Logging Configuration
    # ========================================================================

    LOG_LEVEL: str = "INFO"
    LOG_DIR: Optional[Path] = None
    LOG_ENABLE_CONSOLE: bool = True
    LOG_ENABLE_FILE: bool = True
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    LOG_FORMAT: str = "json"  # json or text

    # ========================================================================
    # Monitoring Configuration
    # ========================================================================

    # Metrics
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090

    # Health Checks
    HEALTH_CHECK_INTERVAL: int = 30  # seconds

    # Performance
    SLOW_REQUEST_THRESHOLD_MS: float = 1000.0
    ENABLE_PERFORMANCE_LOGGING: bool = True

    # ========================================================================
    # Scraping Configuration
    # ========================================================================

    SCRAPER_USER_AGENT: str = "OpenLearn Bot 1.0"
    USER_AGENTS: list[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    SCRAPER_TIMEOUT: int = 30
    REQUEST_TIMEOUT: int = 30  # For aiohttp requests
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_RATE_LIMIT: int = 10  # requests per second
    SCRAPER_CONCURRENT_LIMIT: int = 5
    MAX_CONCURRENT_SCRAPERS: int = 5  # Maximum concurrent scraper threads

    # ========================================================================
    # NLP Configuration
    # ========================================================================

    NLP_MODEL: str = "es_core_news_sm"
    NLP_BATCH_SIZE: int = 32
    NLP_MAX_LENGTH: int = 1000000

    # ========================================================================
    # Task Queue Configuration
    # ========================================================================

    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @property
    def CELERY_BROKER(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def CELERY_BACKEND(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    # ========================================================================
    # Security Configuration
    # ========================================================================

    # CRITICAL: Must be set via environment variable in production
    # Generate with: python backend/scripts/generate_secret_key.py
    # Minimum 32 bytes, 64 bytes recommended for production
    SECRET_KEY: str = Field(
        default="INSECURE_DEFAULT_KEY_REPLACE_IN_PRODUCTION",
        validation_alias="SECRET_KEY",
        description="Cryptographic secret key for JWT signing. MUST be overridden in production."
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    def model_post_init(self, __context) -> None:
        """Validate security-critical settings after initialization."""
        # Enforce SECRET_KEY in production
        if self.ENVIRONMENT.lower() == "production":
            if not self.SECRET_KEY or self.SECRET_KEY == "INSECURE_DEFAULT_KEY_REPLACE_IN_PRODUCTION":
                raise ValueError(
                    "SECRET_KEY must be set via environment variable in production. "
                    "Generate with: python backend/scripts/generate_secret_key.py"
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    f"SECRET_KEY must be at least 32 characters. Current length: {len(self.SECRET_KEY)}. "
                    "Generate with: python backend/scripts/generate_secret_key.py"
                )

            # Enforce database password
            if not self.POSTGRES_PASSWORD or self.POSTGRES_PASSWORD == "openlearn123":
                raise ValueError(
                    "POSTGRES_PASSWORD must be set via environment variable in production. "
                    "Do not use default password."
                )

    # CORS
    CORS_ORIGINS: str | list[str] = Field(
        default="http://localhost:3000",
        validation_alias="ALLOWED_ORIGINS",
        description="CORS origins - accepts string or list"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ========================================================================
    # External Services
    # ========================================================================

    # Sentry (Error Tracking)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0

    # ========================================================================
    # Alerting Configuration
    # ========================================================================

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    ALERT_EMAIL_FROM: Optional[str] = None
    ALERT_EMAIL_TO: list[str] = []

    # Slack
    SLACK_WEBHOOK_URL: Optional[str] = None
    SLACK_CHANNEL: str = "#alerts"

    # ========================================================================
    # Scheduler Configuration
    # ========================================================================

    ENABLE_SCHEDULER: bool = True
    SCRAPING_INTERVAL_MINUTES: int = 30

    # ========================================================================
    # Compression Configuration
    # ========================================================================

    # Enable response compression (Brotli/Gzip)
    ENABLE_COMPRESSION: bool = True

    # Brotli compression level (1-11)
    # 1 = fastest, 11 = best compression
    # Recommended: 4 for balanced performance
    BROTLI_COMPRESSION_LEVEL: int = 4

    # Gzip compression level (1-9)
    # 1 = fastest, 9 = best compression
    # Recommended: 6 for balanced performance
    GZIP_COMPRESSION_LEVEL: int = 6

    # Minimum response size in bytes to trigger compression
    # Smaller responses aren't worth the overhead
    COMPRESSION_MIN_SIZE: int = 500

    # ========================================================================
    # Helper Properties
    # ========================================================================

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
        return self.CORS_ORIGINS

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Global settings instance
settings = Settings()


# ============================================================================
# Environment-Specific Configuration
# ============================================================================

def get_log_config() -> dict:
    """Get logging configuration"""
    return {
        "log_level": settings.LOG_LEVEL,
        "log_dir": settings.LOG_DIR or Path("logs"),
        "enable_console": settings.LOG_ENABLE_CONSOLE,
        "enable_file": settings.LOG_ENABLE_FILE,
        "max_bytes": settings.LOG_MAX_BYTES,
        "backup_count": settings.LOG_BACKUP_COUNT,
    }


def get_db_config() -> dict:
    """Get database configuration"""
    return {
        "url": settings.DATABASE_URL,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "echo": settings.DB_ECHO,
    }


def is_production() -> bool:
    """Check if running in production"""
    return settings.ENVIRONMENT.lower() == "production"


def is_development() -> bool:
    """Check if running in development"""
    return settings.ENVIRONMENT.lower() == "development"


def is_testing() -> bool:
    """Check if running in testing"""
    return settings.ENVIRONMENT.lower() == "testing"
