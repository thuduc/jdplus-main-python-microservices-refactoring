"""Configuration settings."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    RESULT_CACHE_TTL: int = 86400  # 24 hours
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Processing settings
    MAX_SERIES_LENGTH: int = 1000
    PROCESSING_TIMEOUT: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"


settings = Settings()