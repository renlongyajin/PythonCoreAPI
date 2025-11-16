"""用户与角色仓储的行为测试。"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, reset_session_factory
from app.db.init_db import init_db, drop_db


@pytest.fixture(name="db")
def db_session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    """构造独立的内存数据库会话。

    通过 monkeypatch 注入 SQLite 内存连接串，并调用 init_db/drop_db
    保证每个测试互不影响。

    Args:
        monkeypatch (pytest.MonkeyPatch): pytest 提供的环境修改工具。

    Returns:
        Generator[Session, None, None]: 可用于数据库操作的会话生成器。
    """

    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    reset_session_factory()
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        drop_db()


def test_create_user_and_query_by_email(db: Session) -> None:
    """验证创建用户后可通过邮箱查询。

    该用例模拟注册流程，确保仓储写入与查询逻辑一致。

    Args:
        db (Session): 预置的内存数据库会话。
    """

    from app.apps.auth.repository import UserRepository

    user_repo = UserRepository()
    created = user_repo.create(
        db=db,
        email="alice@example.com",
        password_hash="hashed",
        full_name="Alice",
    )

    fetched = user_repo.get_by_email(db, "alice@example.com")
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.full_name == "Alice"


def test_assign_roles_to_user(db: Session) -> None:
    """验证用户角色多对多操作。

    覆盖角色创建与 `set_roles` 的行为，确保关联表写入成功。

    Args:
        db (Session): 预置的内存数据库会话。
    """

    from app.apps.auth.repository import RoleRepository, UserRepository

    role_repo = RoleRepository()
    user_repo = UserRepository()

    admin_role = role_repo.create(db, name="admin")
    editor_role = role_repo.create(db, name="editor")
    user = user_repo.create(db=db, email="bob@example.com", password_hash="hashed")

    user_repo.set_roles(db=db, user=user, role_ids=[admin_role.id, editor_role.id])

    roles = user_repo.list_roles(db=db, user_id=user.id)
    names = {role.name for role in roles}
    assert names == {"admin", "editor"}
