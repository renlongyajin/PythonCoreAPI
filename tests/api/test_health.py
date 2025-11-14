"""健康检查 API 的测试用例。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="module")
def test_client() -> TestClient:
    """构造 FastAPI 测试客户端。"""

    app = create_app()
    return TestClient(app)


def test_health_endpoint_returns_ok_payload(test_client: TestClient) -> None:
    """`GET /api/v1/health` 应返回固定的状态负载。"""

    response = test_client.get("/api/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_name"] == "PythonCoreAPI"
    assert payload["environment"] == "development"
    assert payload["version"] == "v1"


def test_health_endpoint_includes_cache_headers(test_client: TestClient) -> None:
    """响应应声明不可缓存，确保状态实时。"""

    response = test_client.get("/api/v1/health")
    cache_control = response.headers.get("cache-control")
    assert cache_control == "no-store"
