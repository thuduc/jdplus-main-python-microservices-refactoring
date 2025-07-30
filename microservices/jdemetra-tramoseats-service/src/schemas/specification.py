"""TRAMO/SEATS specification schemas."""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class ArimaSpec(BaseModel):
    """ARIMA model specification."""
    p: Optional[int] = Field(None, ge=0, le=3, description="AR order (auto if None)")
    d: Optional[int] = Field(None, ge=0, le=2, description="Differencing order (auto if None)")
    q: Optional[int] = Field(None, ge=0, le=3, description="MA order (auto if None)")
    bp: Optional[int] = Field(None, ge=0, le=1, description="Seasonal AR order")
    bd: Optional[int] = Field(None, ge=0, le=1, description="Seasonal differencing")
    bq: Optional[int] = Field(None, ge=0, le=1, description="Seasonal MA order")
    mean: bool = Field(True, description="Include mean")


class OutlierSpec(BaseModel):
    """Outlier detection specification."""
    enabled: bool = Field(True, description="Enable outlier detection")
    types: List[Literal["AO", "LS", "TC", "SO"]] = Field(
        ["AO", "LS", "TC"],
        description="Outlier types: AO=Additive, LS=Level Shift, TC=Transitory Change, SO=Seasonal"
    )
    critical_value: float = Field(3.5, gt=0, description="Critical value for detection")


class CalendarSpec(BaseModel):
    """Calendar effects specification."""
    trading_days: bool = Field(False, description="Include trading days effect")
    easter: bool = Field(False, description="Include Easter effect")
    leap_year: bool = Field(False, description="Include leap year effect")


class TransformSpec(BaseModel):
    """Transformation specification."""
    function: Literal["none", "log", "auto"] = Field("auto", description="Transformation function")


class DecompositionSpec(BaseModel):
    """SEATS decomposition specification."""
    approximation: Literal["none", "legacy", "noisy"] = Field("legacy", description="Approximation mode")
    ma_unit_root_boundary: float = Field(0.95, gt=0, lt=1, description="MA unit root boundary")
    trend_boundary: float = Field(0.5, gt=0, lt=1, description="Trend boundary")
    seas_boundary: float = Field(0.8, gt=0, lt=1, description="Seasonal boundary")
    seas_boundary_at_pi: float = Field(0.8, gt=0, lt=1, description="Seasonal boundary at PI")


class TramoSeatsSpecification(BaseModel):
    """Complete TRAMO/SEATS specification."""
    arima: ArimaSpec = Field(default_factory=ArimaSpec, description="ARIMA specification")
    outlier: OutlierSpec = Field(default_factory=OutlierSpec, description="Outlier specification")
    calendar: CalendarSpec = Field(default_factory=CalendarSpec, description="Calendar specification")
    transform: TransformSpec = Field(default_factory=TransformSpec, description="Transformation specification")
    decomposition: DecompositionSpec = Field(default_factory=DecompositionSpec, description="Decomposition specification")