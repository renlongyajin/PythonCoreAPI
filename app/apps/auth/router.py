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
    """注册新用户。"""

    user = service.register(db, payload)
    return UserRead.model_validate(user, from_attributes=True)


@router.post("/login", response_model=TokenPair)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(AuthService),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    """登录并返回 token。"""

    user = service.authenticate(db, credentials)
    return service.build_token_pair(user.id, settings)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(
    payload: RefreshRequest,
    service: AuthService = Depends(AuthService),
    settings: Settings = Depends(get_settings),
) -> TokenPair:
    """刷新 access/refresh token。"""

    return service.refresh(payload, settings)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    """返回当前登录用户信息。"""

    return UserRead.model_validate(current_user, from_attributes=True)
