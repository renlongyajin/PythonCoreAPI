"""应用配置定义与依赖。"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """集中管理应用运行所需的环境配置。"""

    app_name: str = "PythonCoreAPI"
    app_env: str = "development"
    api_prefix: str = "/api"
    api_version: str = "v1"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 10080
    database_url: str = "postgresql+psycopg://username:password@localhost:5432/pythoncoreapi"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"
    openai_api_key: str = "sk-placeholder"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """获取全局单例 Settings，避免重复解析 .env。"""

    return Settings()
