import asyncio
from unittest.mock import MagicMock, AsyncMock
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
import pytest_asyncio

from main import app
from src.database.models import Base
from src.database.db import get_db

# 1. Mock Redis client
class MockRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def setex(self, key: str, time: int, value: str):
        self.store[key] = value

    async def delete(self, key: str):
        self.store.pop(key, None)

    async def flushall(self):
        self.store.clear()

mock_redis = MockRedis()

# Override the global redis_client in db.py and services/auth.py
import src.database.db
import src.services.auth
src.database.db.redis_client = mock_redis
src.services.auth.redis_client = mock_redis

# 2. Mock FastMail
@pytest.fixture(autouse=True)
def mock_fastmail(monkeypatch):
    send_message_mock = AsyncMock()
    monkeypatch.setattr("src.services.email.FastMail.send_message", send_message_mock)
    return send_message_mock

# 3. SQLite In-Memory Database for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

# Override the FastAPI db dependency
@pytest.fixture(autouse=True)
def override_db_dependency(monkeypatch, db_session):
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

from httpx import AsyncClient, ASGITransport

@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
