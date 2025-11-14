"""数据库 Session 管理测试。"""

from __future__ import annotations

import importlib

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    """每个测试前后清理配置缓存。"""

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _reload_session_module():
    """重新加载 session 模块以应用最新配置。"""

    import app.db.session as session

    importlib.reload(session)
    return session


def test_session_factory_uses_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """SessionLocal 应绑定到配置指定的数据库。"""

    monkeypatch.setenv("DATABASE_URL", "sqlite:///./pytest.db")
    session = _reload_session_module()

    engine_url = str(session.get_engine().url)
    assert engine_url == "sqlite:///./pytest.db"


def test_get_db_yields_and_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_db 生成器应在使用后关闭 Session。"""

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
