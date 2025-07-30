"""Configuration settings."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/tsdata"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Service settings
    MAX_SERIES_LENGTH: int = 100000
    MAX_BATCH_SIZE: int = 100
    
    class Config:
        env_file = ".env"


settings = Settings()