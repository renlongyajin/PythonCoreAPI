"""管理数据库 Engine 与 Session。"""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings

# 预先创建 sessionmaker，稍后通过 configure 绑定 Engine
SessionLocal = sessionmaker(autoflush=False, autocommit=False)


@lru_cache(maxsize=1)
def _engine_by_url(database_url: str) -> Engine:
    """根据连接字符串构建或复用 Engine。

    Args:
        database_url (str): SQLAlchemy 数据库连接串。

    Returns:
        Engine: 缓存的 Engine 实例。
    """

    return create_engine(database_url, pool_pre_ping=True, future=True)


def get_engine(settings: Settings | None = None) -> Engine:
    """读取配置并返回对应 Engine。

    Args:
        settings (Settings | None): 可选配置实例，默认全局。

    Returns:
        Engine: 绑定到配置数据库的 Engine。
    """

    resolved_settings = settings or get_settings()
    return _engine_by_url(resolved_settings.database_url)


def _configure_sessionmaker(settings: Settings | None = None) -> None:
    """根据配置刷新 SessionLocal 的绑定。

    Args:
        settings (Settings | None): 可选配置，用于选择 Engine。
    """

    SessionLocal.configure(bind=get_engine(settings))


_configure_sessionmaker()


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖使用的数据库 Session 生成器。

    Returns:
        Generator[Session, None, None]: contextmanager 风格的 Session。
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_session_factory() -> None:
    """清空缓存并重新配置 Session 工厂。

    供测试或配置变更后调用，确保新的连接串立即生效。
    """

    get_settings.cache_clear()
    _engine_by_url.cache_clear()
    _configure_sessionmaker()
