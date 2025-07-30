"""Response schemas for ARIMA service."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from jdemetra_common.schemas import ArimaModelSchema, TsPeriodSchema


class EstimateResponse(BaseModel):
    """ARIMA estimation response."""
    
    model_id: UUID = Field(..., description="Model ID for future reference")
    model: ArimaModelSchema = Field(..., description="Estimated ARIMA model")
    fit_time: float = Field(..., description="Fitting time in seconds")
    in_sample_metrics: Dict[str, float] = Field(..., description="In-sample fit metrics")
    convergence_info: Dict[str, Any] = Field(..., description="Convergence information")


class ForecastPoint(BaseModel):
    """Single forecast point."""
    
    period: TsPeriodSchema = Field(..., description="Forecast period")
    forecast: float = Field(..., description="Point forecast")
    lower_bound: float = Field(..., description="Lower confidence bound")
    upper_bound: float = Field(..., description="Upper confidence bound")


class ForecastResponse(BaseModel):
    """Forecast response."""
    
    model_id: UUID = Field(..., description="Model ID used")
    forecasts: List[ForecastPoint] = Field(..., description="Forecast values")
    confidence_level: float = Field(..., description="Confidence level used")
    forecast_time: float = Field(..., description="Forecasting time in seconds")


class IdentifyResponse(BaseModel):
    """Model identification response."""
    
    best_model: ArimaModelSchema = Field(..., description="Best identified model")
    search_summary: Dict[str, Any] = Field(..., description="Search process summary")
    candidates_evaluated: int = Field(..., description="Number of models evaluated")
    identification_time: float = Field(..., description="Identification time in seconds")


class DiagnosticTest(BaseModel):
    """Single diagnostic test result."""
    
    test_name: str = Field(..., description="Test name")
    statistic: float = Field(..., description="Test statistic")
    p_value: float = Field(..., description="P-value")
    conclusion: str = Field(..., description="Test conclusion")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional test details")


class DiagnoseResponse(BaseModel):
    """Model diagnostics response."""
    
    model_id: UUID = Field(..., description="Model ID")
    residual_stats: Dict[str, float] = Field(..., description="Residual statistics")
    diagnostic_tests: List[DiagnosticTest] = Field(..., description="Diagnostic test results")
    model_adequacy: str = Field(..., description="Overall model adequacy assessment")