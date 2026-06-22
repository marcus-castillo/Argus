"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    All values are overridable via environment variables (or a ``.env`` file).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core ---------------------------------------------------------------
    app_name: str = "CiteCheck"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_v1_prefix: str = "/api/v1"

    # --- Database -----------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://citecheck:citecheck@localhost:5432/citecheck",
        description="Async SQLAlchemy DSN (asyncpg driver).",
    )
    db_echo: bool = Field(default=False)
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)

    # --- Uploads ------------------------------------------------------------
    upload_dir: str = Field(default="/data/uploads")
    max_upload_bytes: int = Field(default=25 * 1024 * 1024)  # 25 MiB

    # --- Worker -------------------------------------------------------------
    worker_poll_interval_seconds: float = Field(default=1.0)
    worker_batch_size: int = Field(default=5)
    job_max_attempts: int = Field(default=3)

    # --- Verification engine -----------------------------------------------
    embedding_dim: int = Field(default=384)
    semantic_match_threshold: float = Field(default=0.82)

    # --- CORS ---------------------------------------------------------------
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @property
    def sync_database_url(self) -> str:
        """psycopg2 DSN used by Alembic (which runs synchronously)."""
        return self.database_url.replace("+asyncpg", "+psycopg2")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor (single instance per process)."""
    return Settings()


settings = get_settings()
