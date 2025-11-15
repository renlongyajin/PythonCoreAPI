"""认证相关服务逻辑。"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.apps.auth.models import User
from app.apps.auth.repository import UserRepository
from app.apps.auth.schemas import LoginRequest, RefreshRequest, TokenPair, UserCreate
from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class AuthService:
    """封装用户注册、登录、刷新等业务逻辑。"""

    def __init__(self, user_repo: UserRepository | None = None) -> None:
        self.user_repo = user_repo or UserRepository()

    def register(self, db: Session, data: UserCreate) -> User:
        """注册新用户。"""

        existing = self.user_repo.get_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        hashed = get_password_hash(data.password)
        return self.user_repo.create(
            db=db,
            email=data.email,
            password_hash=hashed,
            full_name=data.full_name,
        )

    def authenticate(self, db: Session, credentials: LoginRequest) -> User:
        """校验邮箱密码，返回用户。"""

        user = self.user_repo.get_by_email(db, credentials.email)
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        return user

    def build_token_pair(self, user_id: int, settings: Settings | None = None) -> TokenPair:
        """生成一对 access/refresh token。"""

        config = settings or get_settings()
        access_token = create_access_token(user_id, config)
        refresh_token = create_refresh_token(user_id, config)
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=config.access_token_expire_minutes * 60,
        )

    def refresh(self, refresh_request: RefreshRequest, settings: Settings | None = None) -> TokenPair:
        """使用 Refresh Token 生成新的 token 对。"""

        config = settings or get_settings()
        payload = decode_token(refresh_request.refresh_token, config)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        return self.build_token_pair(int(user_id), config)
