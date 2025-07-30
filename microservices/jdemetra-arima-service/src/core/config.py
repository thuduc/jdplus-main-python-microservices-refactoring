"""Configuration settings."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    MODEL_CACHE_TTL: int = 86400  # 24 hours
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Model settings
    MAX_FORECAST_HORIZON: int = 365
    MAX_ARIMA_ORDER: int = 5
    
    class Config:
        env_file = ".env"


settings = Settings()