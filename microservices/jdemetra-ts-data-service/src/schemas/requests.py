"""Request schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID

from jdemetra_common.schemas import TsDataSchema


class CreateTimeSeriesRequest(TsDataSchema):
    """Request to create a time series."""
    
    name: Optional[str] = Field(None, description="Optional name for the time series")


class TransformRequest(BaseModel):
    """Request to transform a time series."""
    
    operation: str = Field(..., description="Transformation operation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    
    @validator("operation")
    def validate_operation(cls, v):
        """Validate transformation operation."""
        allowed = ["log", "sqrt", "diff", "seasonal_diff", "standardize", "detrend"]
        if v not in allowed:
            raise ValueError(f"Operation must be one of {allowed}")
        return v


class BatchCreateRequest(BaseModel):
    """Request to create multiple time series."""
    
    series: List[CreateTimeSeriesRequest] = Field(..., description="List of time series to create")
    
    @validator("series")
    def validate_batch_size(cls, v):
        """Validate batch size."""
        from ..core.config import settings
        if len(v) > settings.MAX_BATCH_SIZE:
            raise ValueError(f"Batch size exceeds maximum of {settings.MAX_BATCH_SIZE}")
        return v