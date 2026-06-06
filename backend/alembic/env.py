"""
Alembic environment configuration for Project Capsule.
Uses async SQLAlchemy engine for migrations.
Bootstraps the pgvector extension automatically.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all models so Alembic can detect them
from app.db.base import Base
from app.models import (  # noqa: F401
    User, Project, Source, Conversation,
    Message, MemoryCapsule, Entity, Relationship, Injection
)
from app.core.config import settings

# Alembic config object
config = context.config

# Set the DB URL from settings
config.set_main_option("sqlalchemy.url", settings.sync_database_uri)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(settings.async_database_uri, poolclass=pool.NullPool)

    async with engine.begin() as conn:
        # Ensure pgvector extension exists before any migration
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
