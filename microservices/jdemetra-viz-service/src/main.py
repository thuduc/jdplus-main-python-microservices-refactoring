"""Main application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from .api import viz
from .core.config import settings
from .core.cache import plot_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting Visualization Service...")
    
    yield
    
    # Shutdown
    print("Shutting down Visualization Service...")
    await plot_cache.clear()


app = FastAPI(
    title="JDemetra+ Visualization Service",
    description="Service for generating charts and visualizations",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(viz.router, prefix="/api/v1", tags=["visualization"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "visualization"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "JDemetra+ Visualization Service",
        "version": "0.1.0",
        "endpoints": [
            "/api/v1/viz/timeseries",
            "/api/v1/viz/decomposition",
            "/api/v1/viz/spectrum",
            "/api/v1/viz/diagnostics",
            "/api/v1/viz/forecast",
            "/api/v1/viz/comparison",
            "/api/v1/viz/batch",
            "/api/v1/viz/themes",
            "/api/v1/viz/download/{plot_id}"
        ]
    }