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
    """验证运行环境的 Python 版本。

    单元测试层面确保解释器版本满足项目最低要求，防止开发或 CI
    在错误版本下执行导致潜在兼容性问题。
    """

    assert sys.version_info >= (3, 11), "需要 Python >= 3.11"


@pytest.mark.parametrize("module_name", REQUIRED_MODULES)
def test_required_modules_installed(module_name: str) -> None:
    """逐个检查核心依赖是否安装成功。

    作为环境健康检查，确保 CI/开发机具备 FastAPI、SQLAlchemy 等基础
    依赖，避免后续测试因缺包而中断。

    Args:
        module_name (str): 预期存在的模块名称。
    """

    module = import_module(module_name)  # noqa: F841 保留引用以触发导入
