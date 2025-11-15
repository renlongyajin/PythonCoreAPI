"""FastAPI 依赖定义。"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.apps.auth.repository import UserRepository
from app.apps.auth.models import User
from app.core.config import Settings, get_settings
from app.core.security import decode_token
from app.db.session import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """解析 Access Token 并注入当前用户。

    所有受保护的 API 通过该依赖验证身份，并加载用户实体供路由使用。

    Args:
        token (str): OAuth2PasswordBearer 注入的 Bearer Token。
        db (Session): 数据库会话，用于查询用户。
        settings (Settings): 应用配置，提供 JWT 秘钥等信息。

    Returns:
        User: 验证通过的用户实体，如失败会抛出 HTTPException。
    """

    repo = UserRepository()
    try:
        payload = decode_token(token, settings)
    except Exception as exc:  # noqa: BLE001 捕获 JWT 解码异常
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = repo.get_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
