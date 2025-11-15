"""Auth 模块的 Pydantic 模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """用户注册请求。"""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class LoginRequest(BaseModel):
    """登录请求体。"""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """刷新 Token 请求体。"""

    refresh_token: str


class UserRead(BaseModel):
    """返回给前端的用户信息。"""

    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    """access/refresh token 对。"""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]
    expires_in: int
