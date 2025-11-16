"""Alembic 环境配置。"""

from __future__ import annotations

import pathlib
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

from logging.config import fileConfig

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.db.base import Base  # noqa: E402
from app.db.init_db import import_model_modules  # noqa: E402
from app.core.config import get_settings  # noqa: E402


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import_model_modules()
target_metadata = Base.metadata


def _get_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Offline 模式运行迁移。"""

    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online 模式运行迁移。"""

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
