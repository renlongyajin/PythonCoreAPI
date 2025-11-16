"""全局中间件实现。"""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.logging import reset_trace_id, set_trace_id

LOGGER = logging.getLogger("app.middleware")


class TraceIdMiddleware(BaseHTTPMiddleware):
    """为每个请求注入 trace_id，并写入响应头。"""

    def __init__(self, app: ASGIApp, header_name: str = "X-Trace-Id") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = request.headers.get(self.header_name) or uuid4().hex
        request.state.trace_id = trace_id
        token = set_trace_id(trace_id)

        try:
            response = await call_next(request)
        except Exception:
            LOGGER.exception("Unhandled exception", extra={"path": str(request.url.path)})
            raise
        finally:
            reset_trace_id(token)

        response.headers[self.header_name] = trace_id
        return response
