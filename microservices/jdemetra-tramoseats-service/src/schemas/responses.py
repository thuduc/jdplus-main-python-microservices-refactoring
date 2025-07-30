"""Response schemas for TRAMO/SEATS service."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from jdemetra_common.schemas import TsDataSchema, ArimaModelSchema


class TramoResults(BaseModel):
    """TRAMO model results."""
    
    model: ArimaModelSchema = Field(..., description="Estimated ARIMA model")
    outliers: List[Dict[str, Any]] = Field(..., description="Detected outliers")
    calendar_effects: Optional[Dict[str, Any]] = Field(None, description="Calendar effects")
    regression_effects: Optional[Dict[str, Any]] = Field(None, description="Regression effects")
    residuals: List[float] = Field(..., description="Model residuals")


class SeatsComponent(BaseModel):
    """SEATS decomposition component."""
    
    name: str = Field(..., description="Component name")
    values: List[float] = Field(..., description="Component values")
    properties: Dict[str, Any] = Field(..., description="Component properties")


class SeatsResults(BaseModel):
    """SEATS decomposition results."""
    
    trend: SeatsComponent = Field(..., description="Trend component")
    seasonal: SeatsComponent = Field(..., description="Seasonal component")
    irregular: SeatsComponent = Field(..., description="Irregular component")
    seasonally_adjusted: List[float] = Field(..., description="Seasonally adjusted series")


class ProcessResponse(BaseModel):
    """TRAMO/SEATS processing response."""
    
    result_id: UUID = Field(..., description="Result ID for future reference")
    status: str = Field(..., description="Processing status")
    tramo_results: Optional[TramoResults] = Field(None, description="TRAMO results")
    seats_results: Optional[SeatsResults] = Field(None, description="SEATS results")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    specification_used: Dict[str, Any] = Field(..., description="Specification used")


class AsyncProcessResponse(BaseModel):
    """Asynchronous processing response."""
    
    job_id: UUID = Field(..., description="Job ID to check status")
    status: str = Field("pending", description="Job status")
    message: str = Field(..., description="Status message")


class DiagnosticsResponse(BaseModel):
    """Diagnostics response."""
    
    result_id: UUID = Field(..., description="Result ID")
    seasonality_tests: Optional[Dict[str, Any]] = Field(None, description="Seasonality test results")
    residual_tests: Optional[Dict[str, Any]] = Field(None, description="Residual diagnostic tests")
    spectral_analysis: Optional[Dict[str, Any]] = Field(None, description="Spectral analysis results")
    quality_measures: Dict[str, float] = Field(..., description="Overall quality measures")