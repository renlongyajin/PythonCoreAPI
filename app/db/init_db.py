"""数据库初始化与清理工具。"""

from __future__ import annotations

from functools import lru_cache

from app.db.base import Base
from app.db.session import get_engine


@lru_cache(maxsize=1)
def _import_model_modules() -> None:
    """集中导入所有 ORM 模块。

    通过导入触发表定义注册到 Base.metadata，使用缓存避免重复执行。
    """

    import app.apps.auth.models  # noqa: F401 导入即触发表注册


def init_db() -> None:
    """在当前数据库创建所有表结构。
    """

    _import_model_modules()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """删除所有注册模型对应的表。
    """

    _import_model_modules()
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
