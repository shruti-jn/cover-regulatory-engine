"""
Application configuration using Pydantic Settings.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "cover-regulatory-engine"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/cover"
    DATABASE_PUBLIC_URL: str | None = None

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # External APIs
    GOOGLE_MAPS_API_KEY: str | None = None

    # Vector Store
    VECTOR_DIMENSIONS: int = 1536
    HNSW_M: int = 16
    HNSW_EF_CONSTRUCTION: int = 64

    # Logging
    LOG_LEVEL: str = "INFO"
    STRUCTLOG_FORMAT: str = "json"

    @property
    def async_database_url(self) -> str:
        """Return database URL with asyncpg driver."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
