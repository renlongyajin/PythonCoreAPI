"""中间件与异常处理的集成测试。"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.exception import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import TraceIdMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    configure_logging()
    app.add_middleware(TraceIdMiddleware)
    register_exception_handlers(app)
    return app


def test_trace_id_middleware_sets_header_and_request_state() -> None:
    """trace_id 中间件应写入响应头，且在 request.state 可读。"""

    app = _build_app()

    @app.get("/ping")
    async def ping(request: Request) -> dict[str, str | None]:
        return {"trace_id": getattr(request.state, "trace_id", None)}

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.headers["X-Trace-Id"]
    assert response.json()["trace_id"] == response.headers["X-Trace-Id"]


def test_generic_exception_returns_structured_payload() -> None:
    """未捕获异常需返回统一结构。"""

    app = _build_app()

    @app.get("/boom")
    async def boom() -> None:
        raise ValueError("boom")  # noqa: TRY003 - 测试故意抛错

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/boom")
    data = response.json()
    assert response.status_code == 500
    assert data["code"] == "internal_error"
    assert data["message"]
    assert data["trace_id"]
    assert response.headers["X-Trace-Id"] == data["trace_id"]


def test_validation_error_response_contains_details() -> None:
    """请求参数错误时返回详情。"""

    app = _build_app()

    @app.get("/items/{item_id}")
    async def read_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    client = TestClient(app)
    response = client.get("/items/not-int")
    data = response.json()
    assert response.status_code == 422
    assert data["code"] == "validation_error"
    assert data["details"]
    assert data["trace_id"]
