"""应用日志配置与请求上下文管理。"""

from __future__ import annotations

import json
import logging
from logging.config import dictConfig
from datetime import datetime, timezone
from contextvars import ContextVar, Token
from typing import Any

from app.core.config import Settings

TRACE_ID_CTX: ContextVar[str | None] = ContextVar("trace_id", default=None)


class JsonLogFormatter(logging.Formatter):
    """输出 JSON 结构化日志，自动携带 trace_id。"""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - 简洁描述
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        trace_id = TRACE_ID_CTX.get()
        if trace_id:
            payload["trace_id"] = trace_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings | None = None) -> None:
    """配置全局日志格式与级别。"""

    level = (settings.log_level if settings else "INFO").upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonLogFormatter}},
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {"level": level, "handlers": ["default"]},
        }
    )


def set_trace_id(trace_id: str | None) -> Token:
    """设置当前上下文 trace_id，并返回 token 用于恢复。"""

    return TRACE_ID_CTX.set(trace_id)


def reset_trace_id(token: Token) -> None:
    """利用 token 恢复上一层 trace_id。"""

    TRACE_ID_CTX.reset(token)


def get_trace_id() -> str | None:
    """获取当前上下文 trace_id。"""

    return TRACE_ID_CTX.get()
