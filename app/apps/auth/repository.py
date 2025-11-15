"""用户与角色的数据访问层。"""

from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.apps.auth.models import Role, User, UserRole


class UserRepository:
    """提供用户 CRUD 及角色绑定相关的数据库操作。"""

    def create(
        self,
        db: Session,
        *,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        """创建用户记录并返回实体。

        该方法供注册或后台创建账号时使用，确保所有必要字段写入数据库。

        Args:
            db (Session): 当前数据库会话，负责事务提交。
            email (str): 用户邮箱，需确保唯一。
            password_hash (str): 已加密的密码摘要。
            full_name (str | None): 展示用姓名，可为空。
            is_active (bool): 是否激活，默认 True。

        Returns:
            User: 新建并刷新后的用户 ORM 实体。
        """

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
        """按邮箱检索单个用户。

        主要用于登录或后台查验账号是否存在。

        Args:
            db (Session): 数据库会话对象。
            email (str): 目标邮箱。

        Returns:
            User | None: 匹配的用户对象，未找到返回 None。
        """

        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        """通过主键 ID 查询用户。

        Args:
            db (Session): 数据库会话。
            user_id (int): 用户主键。

        Returns:
            User | None: 查询到的用户实体，否则 None。
        """

        stmt = select(User).where(User.id == user_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_roles(self, db: Session, user_id: int) -> Sequence[Role]:
        """列出指定用户所拥有的角色。

        Args:
            db (Session): 数据库会话。
            user_id (int): 目标用户 ID。

        Returns:
            Sequence[Role]: 用户当前绑定的角色列表。
        """

        stmt = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        return db.execute(stmt).scalars().all()

    def set_roles(self, db: Session, *, user: User, role_ids: Iterable[int]) -> None:
        """为用户重新绑定角色集合。

        在后台分配权限或重置角色时使用，会覆盖用户现有角色。

        Args:
            db (Session): 数据库会话。
            user (User): 目标用户实体。
            role_ids (Iterable[int]): 应绑定的角色 ID 集合。
        """

        stmt = select(Role).where(Role.id.in_(tuple(role_ids) or (-1,)))
        roles = db.execute(stmt).scalars().all()
        user.roles = roles  # type: ignore[assignment] SQLAlchemy 管理关系
        db.add(user)
        db.commit()
        db.refresh(user)


class RoleRepository:
    """封装角色增删改查逻辑。"""

    def create(self, db: Session, *, name: str, description: str | None = None) -> Role:
        """创建新角色并返回实体。

        Args:
            db (Session): 数据库会话。
            name (str): 角色名，需唯一。
            description (str | None): 角色说明，可选。

        Returns:
            Role: 新建并刷新后的角色实体。
        """

        role = Role(name=name, description=description)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
