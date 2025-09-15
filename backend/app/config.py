"""
Configuration management for the platform
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = os.getenv("APP_NAME", "Colombia Intel Platform")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_V1_PREFIX: str = "/api/v1"

    # Security - MUST be set via environment variable in production
    SECRET_KEY: str = os.getenv("SECRET_KEY", None)

    @property
    def get_secret_key(self) -> str:
        """Get secret key with validation."""
        if not self.SECRET_KEY:
            if self.ENVIRONMENT == "production":
                raise ValueError("SECRET_KEY must be set in production environment")
            # Generate a secure random key for development only
            return secrets.token_urlsafe(32)
        return self.SECRET_KEY

    # Database - MUST be configured via environment variable
    DATABASE_URL: str = os.getenv("DATABASE_URL", None)

    @property
    def get_database_url(self) -> str:
        """Get database URL with validation."""
        if not self.DATABASE_URL:
            if self.ENVIRONMENT == "production":
                raise ValueError("DATABASE_URL must be set in production environment")
            # Default for development only
            return "postgresql://localhost/colombia_intel_dev"
        return self.DATABASE_URL

    # Elasticsearch
    ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    ELASTICSEARCH_INDEX: str = "colombia_content"

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Scraping Configuration
    ENABLE_SCHEDULER: bool = True
    SCRAPING_INTERVAL_MINUTES: int = 30
    MAX_CONCURRENT_SCRAPERS: int = 5
    REQUEST_TIMEOUT: int = 30
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    ]

    # NLP Configuration
    SPACY_MODEL: str = "es_core_news_lg"
    MIN_ENTITY_CONFIDENCE: float = 0.7

    # Colombian News Sources
    NEWS_SOURCES: List[dict] = [
        {
            "name": "El Tiempo",
            "url": "https://www.eltiempo.com",
            "category": "national_media",
            "scrape_interval": 30
        },
        {
            "name": "El Espectador",
            "url": "https://www.elespectador.com",
            "category": "national_media",
            "scrape_interval": 30
        },
        {
            "name": "Semana",
            "url": "https://www.semana.com",
            "category": "national_media",
            "scrape_interval": 45
        },
        {
            "name": "La República",
            "url": "https://www.larepublica.co",
            "category": "economic",
            "scrape_interval": 60
        },
        {
            "name": "Presidencia",
            "url": "https://www.presidencia.gov.co",
            "category": "government",
            "scrape_interval": 60
        },
        {
            "name": "MinDefensa",
            "url": "https://www.mindefensa.gov.co",
            "category": "government",
            "scrape_interval": 120
        },
        {
            "name": "DANE",
            "url": "https://www.dane.gov.co",
            "category": "statistics",
            "scrape_interval": 360
        }
    ]

    # Language Learning Configuration
    DIFFICULTY_LEVELS: List[str] = ["beginner", "intermediate", "advanced", "expert"]
    MIN_WORD_FREQUENCY: int = 3
    VOCABULARY_BATCH_SIZE: int = 20

    # Authentication
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()