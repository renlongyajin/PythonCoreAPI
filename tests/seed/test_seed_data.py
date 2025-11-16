"""数据库种子脚本的测试。"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.init_db import import_model_modules
from app.apps.auth.models import Role, User


@pytest.fixture(name="db")
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    """构造用于种子脚本的本地 SQLite Session。

    Args:
        tmp_path (Path): pytest 提供的临时目录，用于存放 sqlite 文件。

    Returns:
        Generator[Session, None, None]: 提供事务管理的 Session。
    """

    db_file = tmp_path / "seed.sqlite"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False}, future=True)
    import_model_modules()
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_seed_base_data_creates_roles_and_admin(db: Session) -> None:
    """首次执行应生成默认角色与管理员。"""

    from scripts.seed_data import seed_base_data

    seed_base_data(db)

    role_names = {row.name for row in db.execute(select(Role)).scalars()}
    assert {"admin", "user"}.issubset(role_names)

    admin = db.execute(select(User).where(User.email == "admin@example.com")).scalar_one()
    assert admin.full_name == "Administrator"
    assert admin.is_active


def test_seed_base_data_is_idempotent(db: Session) -> None:
    """重复执行种子脚本不应创建重复数据。"""

    from scripts.seed_data import seed_base_data

    seed_base_data(db)
    seed_base_data(db)

    roles = db.execute(select(Role)).scalars().all()
    users = db.execute(select(User)).scalars().all()
    assert len(roles) == 2
    assert len(users) == 1
