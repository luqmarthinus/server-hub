import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.mysql import MySqlContainer

from src.core.config import get_settings
from src.main import create_app
from src.core.logging import configure_logging

configure_logging()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mysql_container() -> Generator[MySqlContainer, None, None]:
    with MySqlContainer("mysql:8.0.44") as mysql:
        yield mysql


@pytest.fixture(scope="session")
def database_url(mysql_container: MySqlContainer) -> str:
    url = mysql_container.get_connection_url().replace("mysql+pymysql", "mysql+aiomysql")
    return url


@pytest_asyncio.fixture(scope="session")
async def async_engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(database_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def run_migrations(async_engine: AsyncEngine, database_url: str) -> None:
    import os
    os.environ["DATABASE_URL"] = database_url
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def anyio_backend():
    return "asyncio"
