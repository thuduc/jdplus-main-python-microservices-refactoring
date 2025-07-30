"""Decomposition models and enums."""

from enum import Enum


class ComponentType(str, Enum):
    """Time series component types."""
    
    TREND = "trend"
    SEASONAL = "seasonal"
    IRREGULAR = "irregular"
    TREND_CYCLE = "trend_cycle"
    SEASONALLY_ADJUSTED = "seasonally_adjusted"
    CALENDAR = "calendar"
    OUTLIER = "outlier"


class DecompositionMode(str, Enum):
    """Decomposition mode."""
    
    ADDITIVE = "additive"
    MULTIPLICATIVE = "multiplicative"
    LOG_ADDITIVE = "log_additive"
    PSEUDO_ADDITIVE = "pseudo_additive"