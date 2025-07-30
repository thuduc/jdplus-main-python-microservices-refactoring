"""Response schemas for X-13 service."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from jdemetra_common.schemas import ArimaModelSchema


class RegArimaResults(BaseModel):
    """RegARIMA model results."""
    
    model: ArimaModelSchema = Field(..., description="Estimated ARIMA model")
    regression_effects: Dict[str, Dict[str, float]] = Field(..., description="Regression coefficients")
    outliers: List[Dict[str, Any]] = Field(..., description="Detected outliers")
    transformation: str = Field(..., description="Applied transformation")


class X11Results(BaseModel):
    """X-11 decomposition results."""
    
    d10: List[float] = Field(..., description="Seasonal factors")
    d11: List[float] = Field(..., description="Seasonally adjusted series")
    d12: List[float] = Field(..., description="Trend-cycle")
    d13: List[float] = Field(..., description="Irregular component")
    decomposition_mode: str = Field(..., description="Decomposition mode used")


class SeatsDecomposition(BaseModel):
    """SEATS decomposition results."""
    
    trend: List[float] = Field(..., description="Trend component")
    seasonal: List[float] = Field(..., description="Seasonal component")
    irregular: List[float] = Field(..., description="Irregular component")
    seasonally_adjusted: List[float] = Field(..., description="Seasonally adjusted series")


class ProcessResponse(BaseModel):
    """X-13 processing response."""
    
    result_id: UUID = Field(..., description="Result ID for future reference")
    status: str = Field(..., description="Processing status")
    regarima_results: Optional[RegArimaResults] = Field(None, description="RegARIMA results")
    x11_results: Optional[X11Results] = Field(None, description="X-11 results")
    seats_results: Optional[SeatsDecomposition] = Field(None, description="SEATS results")
    forecasts: Optional[List[Dict[str, Any]]] = Field(None, description="Forecasts")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    specification_used: Dict[str, Any] = Field(..., description="Specification used")


class DiagnosticsResponse(BaseModel):
    """Diagnostics response."""
    
    result_id: UUID = Field(..., description="Result ID")
    spectrum_analysis: Optional[Dict[str, Any]] = Field(None, description="Spectrum analysis")
    stability_tests: Optional[Dict[str, Any]] = Field(None, description="Stability test results")
    residual_diagnostics: Optional[Dict[str, Any]] = Field(None, description="Residual diagnostics")
    sliding_spans: Optional[Dict[str, Any]] = Field(None, description="Sliding spans analysis")
    summary_statistics: Dict[str, float] = Field(..., description="Summary statistics")


class ComparisonResult(BaseModel):
    """Single specification comparison result."""
    
    specification_index: int = Field(..., description="Index of specification")
    aic: Optional[float] = Field(None, description="AIC value")
    bic: Optional[float] = Field(None, description="BIC value")
    ljung_box_pvalue: Optional[float] = Field(None, description="Ljung-Box p-value")
    stability_score: Optional[float] = Field(None, description="Stability score")
    rank: Optional[int] = Field(None, description="Overall rank")


class CompareResponse(BaseModel):
    """Specification comparison response."""
    
    comparison_id: UUID = Field(..., description="Comparison ID")
    results: List[ComparisonResult] = Field(..., description="Comparison results")
    best_specification_index: int = Field(..., description="Index of best specification")
    comparison_summary: Dict[str, Any] = Field(..., description="Summary of comparison")