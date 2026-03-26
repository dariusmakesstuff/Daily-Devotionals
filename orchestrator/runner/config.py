from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Postgres in Docker: postgresql+psycopg://wwm:wwm@localhost:5433/wwm_orchestrator
    # Local dev without Docker: sqlite:///./wwm_dev.db
    database_url: str = "sqlite:///./wwm_dev.db"
    redis_url: str = "redis://localhost:6380/0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    require_human_approval: bool = False
    log_level: str = "INFO"
    # No Redis/Arq: execute pipeline in a background thread from the API process (dev only).
    sync_worker: bool = True

    # Optional live integrations (unset = demo stub for that capability)
    supabase_url: str | None = None
    supabase_service_key: str | None = None
    supabase_editorial_limit: int = 5
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Research / script LLM loops (each revision round = review + optional rewrite call)
    theology_max_revision_rounds: int = 2
    script_guard_max_revision_rounds: int = 2
    research_max_tokens: int = 4096
    script_max_tokens: int = 6144
    theology_review_max_tokens: int = 1536
    script_guard_max_tokens: int = 2048
    planning_context_max_tokens: int = 1536

    # Phase 0: secrets + operator API protection
    encryption_key: str | None = None
    orchestrator_api_key: str | None = None
    artifact_storage_path: str = "./artifact_store"
    rate_limit_per_minute: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
