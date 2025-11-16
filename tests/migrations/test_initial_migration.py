"""Alembic 迁移集成测试。"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(name="alembic_cfg")
def alembic_cfg_fixture(tmp_path: Path) -> Generator[Config, None, None]:
    """提供基于临时 SQLite 的 Alembic 配置。

    该 fixture 为升级/回滚测试创建独立的数据库文件，避免污染本地环境。

    Args:
        tmp_path (Path): pytest 提供的临时目录路径。

    Returns:
        Generator[Config, None, None]: 注入 Alembic Config 的生成器。
    """

    ini_path = PROJECT_ROOT / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    db_path = tmp_path / "alembic.sqlite"
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    yield cfg


def test_upgrade_creates_auth_tables(alembic_cfg: Config) -> None:
    """验证 upgrade head 会创建用户/角色相关表。

    Args:
        alembic_cfg (Config): 临时数据库对应的 Alembic 配置。
    """

    command.upgrade(alembic_cfg, "head")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"users", "roles", "user_roles"}.issubset(tables)

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    expected_user_cols = {"id", "email", "password_hash", "full_name", "is_active", "created_at", "updated_at"}
    assert expected_user_cols.issubset(user_columns)

    email_unique_constraints = [
        constraint
        for constraint in inspector.get_unique_constraints("users")
        if set(constraint.get("column_names", [])) == {"email"}
    ]
    assert email_unique_constraints, "users.email 需具备唯一约束"

    junction_columns = {col["name"] for col in inspector.get_columns("user_roles")}
    assert {"user_id", "role_id"}.issubset(junction_columns)

    junction_unique = [
        constraint
        for constraint in inspector.get_unique_constraints("user_roles")
        if set(constraint.get("column_names", [])) == {"user_id", "role_id"}
    ]
    assert junction_unique, "user_roles 需具备联合唯一约束"


def test_downgrade_drops_tables(alembic_cfg: Config) -> None:
    """验证 downgrade base 会删除用户/角色相关表。

    Args:
        alembic_cfg (Config): 临时数据库对应的 Alembic 配置。
    """

    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" not in tables
    assert "roles" not in tables
    assert "user_roles" not in tables
