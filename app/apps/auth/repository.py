"""用户与角色的数据访问层。"""

from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.models import Role, User, UserRole


class UserRepository:
    """封装用户表的常见操作。"""

    def create(
        self,
        db: Session,
        *,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        """创建并返回用户。"""

        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_by_email(self, db: Session, email: str) -> User | None:
        """通过邮箱查找用户。"""

        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    def list_roles(self, db: Session, user_id: int) -> Sequence[Role]:
        """列出用户角色。"""

        stmt = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        return db.execute(stmt).scalars().all()

    def set_roles(self, db: Session, *, user: User, role_ids: Iterable[int]) -> None:
        """重置用户角色。"""

        stmt = select(Role).where(Role.id.in_(tuple(role_ids) or (-1,)))
        roles = db.execute(stmt).scalars().all()
        user.roles = roles  # type: ignore[assignment] SQLAlchemy 管理关系
        db.add(user)
        db.commit()
        db.refresh(user)


class RoleRepository:
    """角色表的 CRUD。"""

    def create(self, db: Session, *, name: str, description: str | None = None) -> Role:
        """创建角色。"""

        role = Role(name=name, description=description)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
