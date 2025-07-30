"""Main entry point for ARIMA Modeling Service."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from .api import arima
from .core.config import settings


# Global Redis client
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global redis_client
    # Startup
    redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=False)
    yield
    # Shutdown
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="ARIMA Modeling Service",
    description="ARIMA model estimation and forecasting service",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(arima.router, prefix="/api/v1", tags=["arima"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "arima-service"}


def get_redis():
    """Get Redis client."""
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    return redis_client