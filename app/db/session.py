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
    """按连接字符串缓存 Engine，避免重复创建。"""

    return create_engine(database_url, pool_pre_ping=True, future=True)


def get_engine(settings: Settings | None = None) -> Engine:
    """根据配置返回 Engine，默认使用全局 Settings。"""

    resolved_settings = settings or get_settings()
    return _engine_by_url(resolved_settings.database_url)


def _configure_sessionmaker(settings: Settings | None = None) -> None:
    """将 SessionLocal 绑定到最新 Engine。"""

    SessionLocal.configure(bind=get_engine(settings))


_configure_sessionmaker()


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖使用的 Session 生成器。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_session_factory() -> None:
    """测试或运维场景下重建 Engine 与 Session 绑定。"""

    get_settings.cache_clear()
    _engine_by_url.cache_clear()
    _configure_sessionmaker()
