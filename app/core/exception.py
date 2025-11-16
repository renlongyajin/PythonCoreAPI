"""统一异常处理与响应结构。"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_trace_id

LOGGER = logging.getLogger("app.exceptions")


def register_exception_handlers(app: FastAPI) -> None:
    """在 FastAPI 应用上注册统一异常处理。"""

    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _generic_exception_handler)


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    LOGGER.warning("HTTP exception", extra={"status_code": exc.status_code, "detail": exc.detail})
    return _response_with_trace(
        request,
        JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                code="http_error",
                message=str(exc.detail),
                details=None,
                trace_id=_request_trace_id(request),
            ),
        ),
    )


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    LOGGER.warning("Validation error", extra={"errors": exc.errors()})
    return _response_with_trace(
        request,
        JSONResponse(
            status_code=422,
            content=_error_payload(
                code="validation_error",
                message="请求参数校验失败",
                details=exc.errors(),
                trace_id=_request_trace_id(request),
            ),
        ),
    )


async def _generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    LOGGER.exception("Unhandled exception", exc_info=exc)
    return _response_with_trace(
        request,
        JSONResponse(
            status_code=500,
            content=_error_payload(
                code="internal_error",
                message="服务器开小差，请稍后重试",
                details=None,
                trace_id=_request_trace_id(request),
            ),
        ),
    )


def _error_payload(code: str, message: str, details: Any | None, trace_id: str | None = None) -> dict[str, Any]:
    """构造统一的错误响应。"""

    resolved_trace = trace_id or get_trace_id()
    payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "trace_id": resolved_trace,
    }
    if details is not None:
        payload["details"] = details
    return payload


def _response_with_trace(request: Request, response: JSONResponse) -> JSONResponse:
    """将 trace_id 写入响应头，便于链路追踪。"""

    trace_id = getattr(request.state, "trace_id", None) or get_trace_id()
    if trace_id:
        response.headers["X-Trace-Id"] = trace_id
    return response


def _request_trace_id(request: Request) -> str | None:
    """优先从 request.state 读取 trace_id，回退到上下文。"""

    return getattr(request.state, "trace_id", None) or get_trace_id()
