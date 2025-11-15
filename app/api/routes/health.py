"""健康检查路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查", response_model=dict)
def read_health(response: Response, settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """返回应用当前状态。

    Args:
        response (Response): FastAPI 响应对象，用于设置缓存头。
        settings (Settings): 配置实例，提供元数据。

    Returns:
        dict[str, str]: 健康状态及元信息。
    """

    response.headers["Cache-Control"] = "no-store"  # 防止客户端缓存
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "version": settings.api_version,
    }
