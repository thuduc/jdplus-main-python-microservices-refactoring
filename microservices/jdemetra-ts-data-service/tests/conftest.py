"""Test configuration."""

import asyncio
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.main import app
from src.db.connection import Base, get_db, get_redis
from src.core.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    """Override database dependency for tests."""
    async with TestSessionLocal() as session:
        yield session


class MockRedis:
    """Mock Redis client for testing."""
    
    def __init__(self):
        self.data = {}
    
    async def get(self, key: str):
        return self.data.get(key)
    
    async def setex(self, key: str, ttl: int, value: str):
        self.data[key] = value
    
    async def delete(self, key: str):
        self.data.pop(key, None)
    
    async def close(self):
        pass


mock_redis = MockRedis()


def override_get_redis():
    """Override Redis dependency for tests."""
    return mock_redis


# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis] = override_get_redis


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_db():
    """Create test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_timeseries_data():
    """Sample time series data for testing."""
    return {
        "values": [100.0, 102.5, 98.3, 105.2, 107.8, 103.5],
        "start_period": {
            "year": 2023,
            "period": 1,
            "frequency": "M"
        },
        "frequency": "M",
        "metadata": {"source": "test"},
        "name": "Test Series"
    }