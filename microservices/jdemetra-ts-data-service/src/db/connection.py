"""Database connection management."""

from typing import Optional
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from ..core.config import settings

# SQLAlchemy setup
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Redis client
redis_client: Optional[redis.Redis] = None


async def init_db():
    """Initialize database connections."""
    global redis_client
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis
    redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_db():
    """Close database connections."""
    global redis_client
    
    await engine.dispose()
    
    if redis_client:
        await redis_client.close()


async def get_db():
    """Get database session."""
    async with async_session() as session:
        yield session


def get_redis() -> redis.Redis:
    """Get Redis client."""
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    return redis_client