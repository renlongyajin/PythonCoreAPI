"""用户与角色仓储的行为测试。"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, reset_session_factory
from app.db.init_db import init_db, drop_db


@pytest.fixture(name="db")
def db_session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    """使用内存 SQLite 构造独立 Session。"""

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
    """创建用户后应能通过邮箱查询。"""

    from app.apps.auth.repository import RoleRepository, UserRepository

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
    """用户与角色的多对多关联应能写入与读取。"""

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
