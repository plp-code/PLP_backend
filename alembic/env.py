import asyncio
import os
import ssl
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Make `src.python.app...` importable when Alembic runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.python.app.core.config import settings
from src.python.app.core.database import Base
from src.python.app import models  # noqa: F401  (registers every table on Base.metadata)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Pull the connection URL from app settings (.env) rather than hardcoding it.
# ALEMBIC_DATABASE_URL overrides it (used to generate the baseline against a
# throwaway empty schema without touching the real database).
config.set_main_option(
    "sqlalchemy.url", os.getenv("ALEMBIC_DATABASE_URL", settings.DATABASE_URL)
)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata for 'autogenerate' support.
target_metadata = Base.metadata


def _connect_args() -> dict:
    """Match the SSL handling used by the app's engine (DigitalOcean MySQL)."""
    if settings.DB_SSL_REQUIRED and "aiomysql" in settings.DATABASE_URL:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        return {"ssl": ssl_ctx}
    return {}


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no DBAPI)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        # compare_server_default left off: func.now() vs MySQL CURRENT_TIMESTAMP
        # are equivalent but compared unequal, producing false-positive diffs.
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # compare_server_default left off: func.now() vs MySQL CURRENT_TIMESTAMP
        # are equivalent but compared unequal, producing false-positive diffs.
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async Engine and associate a connection with the context."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=_connect_args(),
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
