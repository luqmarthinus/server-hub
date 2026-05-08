# migrations/env.py
from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

from src.core.database import Base

# Import all models so that Base.metadata knows about them
from src.models.user import User  # noqa: F401
from src.models.report import ServerReport  # noqa: F401

# this is the Alembic Config object, which provides access to the .ini file
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for 'autogenerate' support
target_metadata = Base.metadata


def get_sync_database_url() -> str:
    """
    Returns a synchronous database URL suitable for Alembic.
    - If SYNC_DATABASE_URL is set, use it.
    - Otherwise, take DATABASE_URL and replace 'aiomysql' with 'pymysql'.
    - If neither is set, fall back to the url in alembic.ini.
    """
    sync_url = os.getenv("SYNC_DATABASE_URL")
    if sync_url:
        return sync_url

    async_url = os.getenv("DATABASE_URL")
    if async_url:
        # Convert async driver to sync driver
        return async_url.replace("mysql+aiomysql://", "mysql+pymysql://")

    # Fallback to the value in alembic.ini
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_sync_database_url()
    if not url:
        raise ValueError("No database URL found for offline migration.")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a synchronous engine."""
    sync_url = get_sync_database_url()
    if not sync_url:
        raise ValueError(
            "No database URL found. Set SYNC_DATABASE_URL or DATABASE_URL "
            "environment variable, or configure sqlalchemy.url in alembic.ini"
        )

    # Build a configuration dictionary for the engine
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = sync_url

    # Create a synchronous engine
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