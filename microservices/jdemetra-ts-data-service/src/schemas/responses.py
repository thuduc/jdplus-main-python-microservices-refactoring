"""Response schemas."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from jdemetra_common.schemas import TsDataSchema


class TimeSeriesResponse(TsDataSchema):
    """Time series response."""
    
    id: UUID = Field(..., description="Time series ID")
    name: Optional[str] = Field(None, description="Time series name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class TimeSeriesListResponse(BaseModel):
    """List of time series."""
    
    series: List[TimeSeriesResponse] = Field(..., description="List of time series")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


class ValidationResponse(BaseModel):
    """Validation response."""
    
    valid: bool = Field(..., description="Whether the time series is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")