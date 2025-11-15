"""安全相关的通用工具函数。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import Settings, get_settings


def get_password_hash(password: str) -> str:
    """基于 bcrypt 生成密码哈希。"""

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """校验平文密码与哈希是否匹配。"""

    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_token(subject: int, minutes: int, token_type: str, settings: Settings) -> str:
    """创建带过期时间与类型标记的 JWT。"""

    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(user_id: int, settings: Settings | None = None) -> str:
    """生成 Access Token。"""

    config = settings or get_settings()
    return _create_token(user_id, config.access_token_expire_minutes, "access", config)


def create_refresh_token(user_id: int, settings: Settings | None = None) -> str:
    """生成 Refresh Token。"""

    config = settings or get_settings()
    return _create_token(user_id, config.refresh_token_expire_minutes, "refresh", config)


def decode_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """解码并返回 JWT 负载。"""

    config = settings or get_settings()
    return jwt.decode(token, config.secret_key, algorithms=["HS256"])
