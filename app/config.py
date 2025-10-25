"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
import os
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from dotenv import load_dotenv

load_dotenv()


def _get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AppConfig(BaseModel):
    """Typed configuration for the service."""

    model_config = ConfigDict(frozen=True)

    port: int = Field(default=8080, ge=1, le=65535)
    log_level: str = Field(default="INFO")

    slack_bot_token: str = Field(min_length=1)
    slack_post_as_user: bool = Field(default=False)

    supabase_url: HttpUrl
    supabase_anon_key: str | None = None
    supabase_service_role_key: str = Field(min_length=1)
    supabase_schema: str = Field(default="public", min_length=1)
    supabase_table: str = Field(default="kb", min_length=1)
    supabase_search_function: str = Field(default="match_memories", min_length=1)

    embedding_api_url: HttpUrl
    embedding_api_key: str = Field(min_length=1)
    embedding_dim: int = Field(default=1536, gt=0)


@lru_cache(maxsize=1)
def get_settings() -> AppConfig:
    """Load and cache application settings."""

    data = {
        "port": int(os.getenv("PORT", "8080")),
        "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
        "slack_bot_token": os.getenv("SLACK_BOT_TOKEN"),
        "slack_post_as_user": _get_bool(os.getenv("SLACK_POST_AS_USER"), False),
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY"),
        "supabase_service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "supabase_schema": os.getenv("SUPABASE_SCHEMA", "public"),
        "supabase_table": os.getenv("SUPABASE_TABLE", "kb"),
        "supabase_search_function": os.getenv("SUPABASE_SEARCH_FUNCTION", "match_memories"),
        "embedding_api_url": os.getenv("EMBEDDING_API_URL"),
        "embedding_api_key": os.getenv("EMBEDDING_API_KEY"),
        "embedding_dim": int(os.getenv("EMBEDDING_DIM", "1536")),
    }
    return AppConfig(**data)


settings = get_settings()
