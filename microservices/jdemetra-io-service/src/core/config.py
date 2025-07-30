"""Configuration settings."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "jdemetra-data"
    MINIO_SECURE: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # File settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls", ".json", ".xml", ".yaml", ".yml"]
    TEMP_DIR: str = "/tmp/jdemetra-io"
    
    # Processing settings
    CHUNK_SIZE: int = 8192
    MAX_SERIES_PER_FILE: int = 1000
    
    class Config:
        env_file = ".env"


settings = Settings()