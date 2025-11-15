"""数据库 Session 管理测试。"""

from __future__ import annotations

from collections.abc import Generator
import importlib

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache() -> Generator[None, None, None]:
    """在测试用例前后清空 Settings 缓存。

    Returns:
        Generator[None, None, None]: fixture 生命周期管理器。
    """

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _reload_session_module():
    """重新加载数据库 session 模块。

    Returns:
        module: 重新导入后的 session 模块。
    """

    import app.db.session as session

    importlib.reload(session)
    return session


def test_session_factory_uses_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 SessionLocal 绑定的数据库 URL。

    Args:
        monkeypatch (pytest.MonkeyPatch): 注入环境变量。
    """

    monkeypatch.setenv("DATABASE_URL", "sqlite:///./pytest.db")
    session = _reload_session_module()

    engine_url = str(session.get_engine().url)
    assert engine_url == "sqlite:///./pytest.db"


def test_get_db_yields_and_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """确保 get_db 生成器会关闭 Session。

    Args:
        monkeypatch (pytest.MonkeyPatch): 注入环境变量。
    """

    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    session = _reload_session_module()

    generator = session.get_db()
    db = next(generator)
    assert str(db.get_bind().url) == "sqlite:///:memory:"
    assert db.is_active is True

    from unittest.mock import patch

    with patch.object(db, "close", wraps=db.close) as close_mock:
        with pytest.raises(StopIteration):
            next(generator)

        close_mock.assert_called_once()
