"""验证运行环境与核心依赖可用。"""

from importlib import import_module
import sys

import pytest

REQUIRED_MODULES = (
    "fastapi",
    "sqlalchemy",
    "redis",
    "celery",
    "jwt",  # PyJWT 的导入名是 jwt
    "bcrypt",
    "httpx",
    "pgvector",
)


def test_python_version() -> None:
    """确保 Python 版本不低于 3.11."""

    assert sys.version_info >= (3, 11), "需要 Python >= 3.11"


@pytest.mark.parametrize("module_name", REQUIRED_MODULES)
def test_required_modules_installed(module_name: str) -> None:
    """逐个验证关键依赖可被导入."""

    module = import_module(module_name)  # noqa: F841 保留引用以触发导入
