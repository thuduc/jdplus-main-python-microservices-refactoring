"""Service configuration."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service settings."""
    
    # Service
    SERVICE_NAME: str = "jdemetra-viz-service"
    SERVICE_PORT: int = 8008
    
    # Plot settings
    DEFAULT_DPI: int = 100
    DEFAULT_FIGURE_SIZE: tuple = (10, 6)
    MAX_PLOT_SIZE: int = 2000  # Max width/height in pixels
    MAX_SERIES_LENGTH: int = 10000
    
    # Cache
    PLOT_CACHE_TTL: int = 3600  # 1 hour
    PLOT_CACHE_DIR: str = "/tmp/plots"
    MAX_CACHE_SIZE: int = 100  # Max number of cached plots
    
    # Output formats
    SUPPORTED_FORMATS: list = ["png", "svg", "pdf", "html"]
    DEFAULT_FORMAT: str = "png"
    
    # Themes
    DEFAULT_THEME: str = "seaborn"
    AVAILABLE_THEMES: list = [
        "default", "seaborn", "ggplot", "bmh", 
        "dark_background", "grayscale"
    ]
    
    # Plotly settings
    PLOTLY_RENDERER: str = "browser"
    
    class Config:
        env_prefix = "VIZ_"


settings = Settings()