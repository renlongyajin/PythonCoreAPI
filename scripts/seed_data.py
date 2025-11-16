"""数据库种子数据脚本。"""

from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.models import Role, User
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.db.init_db import import_model_modules

DEFAULT_ROLES: tuple[tuple[str, str], ...] = (
    ("admin", "系统管理员"),
    ("user", "普通用户"),
)


def seed_roles(session: Session, roles: Iterable[tuple[str, str]] = DEFAULT_ROLES) -> None:
    """确保指定角色存在，不存在则创建。

    Args:
        session (Session): 数据库会话对象。
        roles (Iterable[tuple[str, str]]): (name, description) 列表。
    """

    for name, description in roles:
        exists = session.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
        if exists:
            continue
        session.add(Role(name=name, description=description))
    session.commit()


def seed_admin_user(
    session: Session,
    *,
    email: str,
    password: str,
    full_name: str = "Administrator",
    role_name: str = "admin",
) -> None:
    """创建默认管理员账号（若不存在）。

    Args:
        session (Session): 数据库会话对象。
        email (str): 管理员邮箱。
        password (str): 明文密码，将在函数内加密。
        full_name (str): 管理员显示名称。
        role_name (str): 需绑定的角色名。
    """

    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    role = session.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
    if role is None:
        raise ValueError(f"Role '{role_name}' 未找到，请先调用 seed_roles")

    if user:
        if role not in user.roles:
            user.roles.append(role)
        session.commit()
        return

    hashed = get_password_hash(password)
    user = User(email=email, password_hash=hashed, full_name=full_name, is_active=True)
    user.roles.append(role)
    session.add(user)
    session.commit()


def seed_base_data(
    session: Session,
    *,
    admin_email: str = "admin@example.com",
    admin_password: str = "Admin123!",
    admin_full_name: str = "Administrator",
) -> None:
    """执行基础种子任务：角色 + 管理员。

    Args:
        session (Session): 数据库会话。
        admin_email (str): 管理员邮箱。
        admin_password (str): 管理员密码。
        admin_full_name (str): 管理员显示名。
    """

    seed_roles(session)
    seed_admin_user(
        session,
        email=admin_email,
        password=admin_password,
        full_name=admin_full_name,
    )


def main() -> None:
    """CLI 入口：连接数据库并写入默认数据。"""

    import_model_modules()
    with SessionLocal() as session:
        seed_base_data(session)


if __name__ == "__main__":
    main()
