"""Main entry point for Data I/O Service."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio

from .api import io
from .core.config import settings


# Global MinIO client
minio_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global minio_client
    # Startup
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    
    # Create bucket if it doesn't exist
    if not minio_client.bucket_exists(settings.MINIO_BUCKET):
        minio_client.make_bucket(settings.MINIO_BUCKET)
    
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Data I/O Service",
    description="Data import/export service for JDemetra+",
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
app.include_router(io.router, prefix="/api/v1", tags=["io"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "io-service"}


def get_minio():
    """Get MinIO client."""
    if not minio_client:
        raise RuntimeError("MinIO not initialized")
    return minio_client