"""Application Configuration and Environment Settings for RAGShield Backend.

Uses pydantic-settings to validate environment variables with strict typing,
safe defaults, and environment file loading.
"""

from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Workspace root path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Core application settings and secrets configuration."""
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # General App Information
    PROJECT_NAME: str = "RAGShield Security Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database Configuration (Defaults to async SQLite for local dev, PostgreSQL in Docker)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/ragshield.db",
        description="Async database connection string"
    )

    # Security & JWT Token Authentication
    SECRET_KEY: str = Field(
        default="synthetic-dev-jwt-secret-key-change-in-production-ragshield-2026",
        description="Cryptographic secret used to sign JWT tokens"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Scan Engine Defaults
    ALLOW_LOCAL_TARGETS: bool = True
    DEFAULT_MAX_CONCURRENCY: int = 3
    DEFAULT_TIMEOUT_SECONDS: float = 15.0
    DEMO_RAG_API_KEY: str = "demo_synthetic_insecure_key_for_testing"

    @property
    def is_sqlite(self) -> bool:
        """Helper to determine whether the configured database dialect is SQLite."""
        return "sqlite" in self.DATABASE_URL.lower()


settings = Settings()
