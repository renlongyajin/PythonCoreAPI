"""FastAPI 应用入口。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.apps.auth.router import router as auth_router
from app.core.config import Settings, get_settings


def create_app() -> FastAPI:
    """构建并返回 FastAPI 应用实例。

    Returns:
        FastAPI: 已注册中间件与路由的应用。
    """

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.api_version)

    _register_middlewares(app)
    _register_routes(app, settings)
    return app


def _register_middlewares(app: FastAPI) -> None:
    """注册全局中间件，如 CORS。"

    Args:
        app (FastAPI): 目标应用实例。
    """

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_routes(app: FastAPI, settings: Settings) -> None:
    """结合配置挂载各功能路由。

    Args:
        app (FastAPI): 应用实例。
        settings (Settings): 配置，用于确定前缀。
    """

    api_prefix = f"{settings.api_prefix}/{settings.api_version}"  # 统一 API 版本路径
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(auth_router, prefix=api_prefix)
