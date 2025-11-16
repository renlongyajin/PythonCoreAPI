"""应用配置定义与依赖。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """集中管理应用全局配置。

    用于加载 .env 及环境变量，向 FastAPI 依赖注入提供统一数据源。
    """

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
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """返回缓存的 Settings 单例。

    FastAPI 依赖会调用此函数，确保配置只解析一次，提升性能。

    Returns:
        Settings: 已加载且缓存的配置实例。
    """

    return Settings(_env_file=_resolve_env_files())


def _resolve_env_files() -> tuple[str, ...]:
    """根据 APP_ENV/APP_ENV_FILE 推导优先级化的 env 文件列表。"""

    override = os.getenv("APP_ENV_FILE")
    if override:
        files = [path.strip() for path in override.split(",") if path.strip()]
        return tuple(files)

    files: list[str] = []
    default_file = BASE_DIR / ".env"
    files.append(str(default_file))

    env_name = os.getenv("APP_ENV")
    if env_name:
        candidate = BASE_DIR / f".env.{env_name}"
        if candidate.exists():
            files.append(str(candidate))

    return tuple(files)
