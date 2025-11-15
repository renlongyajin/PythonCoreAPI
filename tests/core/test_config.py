"""Settings 配置的测试确保读取与缓存行为正确。"""

from __future__ import annotations

from collections.abc import Generator

import pytest

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Generator[None, None, None]:
    """自动清理 Settings 缓存。

    Returns:
        Generator[None, None, None]: fixture 管理的上下文。
    """

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_settings_values() -> None:
    """验证默认配置值与文档一致。"""

    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "PythonCoreAPI"
    assert settings.app_env == "development"
    assert settings.api_prefix == "/api"
    assert settings.api_version == "v1"
    assert settings.database_url.startswith("postgresql+psycopg")


def test_settings_reads_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证环境变量可覆盖默认配置。

    Args:
        monkeypatch (pytest.MonkeyPatch): 注入的环境变量工具。
    """

    monkeypatch.setenv("APP_NAME", "TestAPI")
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("API_VERSION", "v2")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")

    settings = get_settings()
    assert settings.app_name == "TestAPI"
    assert settings.app_env == "staging"
    assert settings.api_version == "v2"
    assert settings.database_url == "sqlite:///./test.db"


def test_get_settings_returns_cached_instance() -> None:
    """验证 Settings 缓存行为。"""

    first = get_settings()
    second = get_settings()
    assert first is second
