from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Analysis API"
    openai_api_key: str = ""
    openai_model: str = "gpt-6-luna"
    ai_provider: Literal["openai", "ollama", "fake"] = "ollama"
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen3.5:9b"
    ollama_timeout_seconds: float = 180.0
    database_url: str = "postgresql+asyncpg://app:app@db:5432/app"
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 3600
    enable_computer_control: bool = False
    allowed_apps: str = "Activity Monitor,Safari,System Settings"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
