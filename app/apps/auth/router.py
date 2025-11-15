"""Auth 相关 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.apps.auth.models import User
from app.apps.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserRead,
)
from app.apps.auth.service import AuthService
from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_user
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    service: AuthService = Depends(AuthService),
) -> UserRead:
    """注册新用户并返回基础信息。

    Args:
        payload (UserCreate): 注册表单，包含邮箱、密码、姓名。
        db (Session): 注入的数据库会话。
        service (AuthService): 认证业务服务。

    Returns:
        UserRead: 新建用户的对外数据。
    """

    user = service.register(db, payload)
    return UserRead.model_validate(user, from_attributes=True)


@router.post("/login", response_model=TokenPair)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(AuthService),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    """校验凭证并返回 token 对。

    Args:
        credentials (LoginRequest): 登录邮箱与密码。
        db (Session): 数据库会话。
        service (AuthService): 认证服务实例。
        settings (Settings): 应用配置。

    Returns:
        TokenPair: 包含 access/refresh token 的响应。
    """

    user = service.authenticate(db, credentials)
    return service.build_token_pair(user.id, settings)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(
    payload: RefreshRequest,
    service: AuthService = Depends(AuthService),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    """使用 refresh token 获取新的 token 对。

    Args:
        payload (RefreshRequest): 携带 refresh token 的请求体。
        service (AuthService): 认证服务。
        settings (Settings): 应用配置。

    Returns:
        TokenPair: 新生成的 token 对。
    """

    return service.refresh(payload, settings)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    """返回当前登录用户的信息。

    Args:
        current_user (User): 通过依赖注入得到的用户实体。

    Returns:
        UserRead: 当前用户的基本资料。
    """

    return UserRead.model_validate(current_user, from_attributes=True)
