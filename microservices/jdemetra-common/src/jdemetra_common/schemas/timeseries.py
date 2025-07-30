"""Pydantic schemas for time series data."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from ..models.timeseries import TsFrequency


class TsPeriodSchema(BaseModel):
    """Schema for time period."""
    
    year: int = Field(..., description="Year")
    period: int = Field(..., ge=1, description="Period within year")
    frequency: TsFrequency = Field(..., description="Time series frequency")
    
    @validator("period")
    def validate_period(cls, v, values):
        """Validate period is within valid range for frequency."""
        if "frequency" in values:
            freq = values["frequency"]
            max_period = freq.periods_per_year
            if v > max_period:
                raise ValueError(f"Period {v} exceeds maximum {max_period} for frequency {freq}")
        return v


class TsDataSchema(BaseModel):
    """Schema for time series data."""
    
    values: List[float] = Field(..., description="Time series values")
    start_period: TsPeriodSchema = Field(..., description="Starting period")
    frequency: TsFrequency = Field(..., description="Time series frequency")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")
    
    @validator("values")
    def validate_values(cls, v):
        """Validate values list is not empty."""
        if not v:
            raise ValueError("Values list cannot be empty")
        return v
    
    class Config:
        json_encoders = {
            TsFrequency: lambda v: v.value
        }