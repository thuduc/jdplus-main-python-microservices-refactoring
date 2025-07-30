"""Main entry point for Statistical Analysis Service."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import stats

app = FastAPI(
    title="Statistical Analysis Service",
    description="Statistical analysis and testing service for JDemetra+",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stats.router, prefix="/api/v1", tags=["statistics"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "stats-service"}