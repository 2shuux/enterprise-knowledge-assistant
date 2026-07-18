"""Application configuration.

All settings are loaded from environment variables (or a local `.env` file).
This is the 12-factor pattern: the same code runs in dev, CI and prod —
only the environment changes. Never hardcode secrets in code.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "Enterprise Knowledge Assistant"
    app_env: str = "development"  # development | test | production
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # --- Infrastructure (used from Milestone 1 onwards) ---
    database_url: str = "postgresql+asyncpg://eka:eka@localhost:5432/eka"
    redis_url: str = "redis://localhost:6379/0"
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # --- Auth (Milestone 1) ---
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    first_user_is_admin: bool = True  # bootstrap: first registered account becomes ADMIN

    # --- AI providers (used from Milestone 2 onwards) ---
    llm_provider: str = "gemini"  # gemini | openai | anthropic
    gemini_api_key: str = ""
    embedding_model: str = "gemini-embedding-001"
    chat_model: str = "gemini-2.5-flash"

    # --- RAG (Milestone 3) ---
    retrieval_k: int = 6  # chunks fed to the LLM per question

    # --- Ingestion (Milestone 2) ---
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MB
    chunk_size_chars: int = 3200   # ~800 tokens (≈4 chars/token)
    chunk_overlap_chars: int = 480  # ~120 tokens

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — parsing the environment once per process."""
    return Settings()
