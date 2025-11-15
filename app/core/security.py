"""安全相关的通用工具函数。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import Settings, get_settings


def get_password_hash(password: str) -> str:
    """生成用户密码的 bcrypt 哈希值。

    供注册或修改密码流程调用，严格使用 UTF-8 编码避免跨平台差异。

    Args:
        password (str): 明文密码。

    Returns:
        str: bcrypt 生成的哈希字符串。
    """

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """校验密码是否与哈希匹配。

    登录流程调用该函数确认凭证有效。

    Args:
        password (str): 用户输入的明文密码。
        hashed_password (str): 数据库存储的哈希值。

    Returns:
        bool: True 表示匹配成功。
    """

    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_token(subject: int, minutes: int, token_type: str, settings: Settings) -> str:
    """内部辅助函数，生成特定类型的 JWT。

    Args:
        subject (int): JWT `sub` 字段，通常为用户 ID。
        minutes (int): 有效期（分钟）。
        token_type (str): access 或 refresh 类型标识。
        settings (Settings): 应用配置，提供秘钥与过期策略。

    Returns:
        str: 编码后的 JWT 字符串。
    """

    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(user_id: int, settings: Settings | None = None) -> str:
    """生成 Access Token。

    供登录或刷新接口使用，为短期访问受保护 API 的凭证。

    Args:
        user_id (int): 目标用户 ID。
        settings (Settings | None): 可选配置，默认取全局设置。

    Returns:
        str: 编码完成的 Access Token。
    """

    config = settings or get_settings()
    return _create_token(user_id, config.access_token_expire_minutes, "access", config)


def create_refresh_token(user_id: int, settings: Settings | None = None) -> str:
    """生成 Refresh Token。

    用于获取新 access token 的长生命周期凭证。

    Args:
        user_id (int): 目标用户 ID。
        settings (Settings | None): 可选配置，默认全局。

    Returns:
        str: 刷新 token 字符串。
    """

    config = settings or get_settings()
    return _create_token(user_id, config.refresh_token_expire_minutes, "refresh", config)


def decode_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """解析 JWT 并返回 payload。

    Args:
        token (str): 待验证的 JWT。
        settings (Settings | None): 可选配置。

    Returns:
        dict[str, Any]: 解码后的 payload 字典。
    """

    config = settings or get_settings()
    return jwt.decode(token, config.secret_key, algorithms=["HS256"])
