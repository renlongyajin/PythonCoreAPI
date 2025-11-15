"""Auth API 集成测试。"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.db.init_db import drop_db, init_db
from app.db.session import reset_session_factory


@pytest.fixture(name="client")
def client_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[TestClient, None, None]:
    """构造携带独立数据库的 TestClient。

    Args:
        monkeypatch (pytest.MonkeyPatch): 环境变量注入工具。
        tmp_path (Path): pytest 提供的临时目录。
    """

    db_file = tmp_path / "auth.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    reset_session_factory()
    init_db()

    app = create_app()
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        drop_db()


def _register_user(client: TestClient, email: str = "user@example.com", password: str = "StrongPass123") -> None:
    """辅助函数：注册测试用户。

    Args:
        client (TestClient): FastAPI 测试客户端。
        email (str): 注册邮箱。
        password (str): 明文密码。
    """
    payload = {"email": email, "password": password, "full_name": "Tester"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201


def test_register_user_returns_basic_profile(client: TestClient) -> None:
    """验证注册接口返回的用户资料。

    Args:
        client (TestClient): 测试客户端。
    """

    payload = {"email": "alice@example.com", "password": "Aa123456", "full_name": "Alice"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == "Alice"
    assert "password" not in data


def test_register_duplicate_email_returns_400(client: TestClient) -> None:
    """重复邮箱注册应提示 400。

    Args:
        client (TestClient): 测试客户端。
    """

    _register_user(client, email="bob@example.com")
    payload = {"email": "bob@example.com", "password": "Aa123456", "full_name": "Bob"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


def test_login_returns_tokens(client: TestClient) -> None:
    """验证登录接口返回 token 对。

    Args:
        client (TestClient): 测试客户端。
    """

    _register_user(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    tokens = response.json()
    assert tokens["token_type"] == "bearer"
    assert "access_token" in tokens and "refresh_token" in tokens


def test_me_endpoint_requires_authentication(client: TestClient) -> None:
    """确保 /me 需要合法的 Bearer Token。

    Args:
        client (TestClient): 测试客户端。
    """

    _register_user(client)
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123"},
    )
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    profile = me_resp.json()
    assert profile["email"] == "user@example.com"


def test_refresh_returns_new_tokens(client: TestClient) -> None:
    """验证 refresh 接口返回新的 token 对。

    Args:
        client (TestClient): 测试客户端。
    """

    _register_user(client)
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    body = refresh_resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
