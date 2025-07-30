"""Request schemas for ARIMA service."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator
from uuid import UUID

from jdemetra_common.schemas import TsDataSchema, ArimaOrderSchema


class EstimateRequest(BaseModel):
    """Request to estimate ARIMA model."""
    
    timeseries: TsDataSchema = Field(..., description="Time series data")
    order: Optional[ArimaOrderSchema] = Field(None, description="ARIMA order (auto if not provided)")
    method: Literal["css", "mle", "css-mle"] = Field("css-mle", description="Estimation method")
    include_mean: bool = Field(True, description="Include mean in model")
    
    @validator("order")
    def validate_order(cls, v):
        """Validate ARIMA order."""
        from ..core.config import settings
        if v:
            if v.p > settings.MAX_ARIMA_ORDER or v.q > settings.MAX_ARIMA_ORDER:
                raise ValueError(f"Order exceeds maximum of {settings.MAX_ARIMA_ORDER}")
        return v


class ForecastRequest(BaseModel):
    """Request to generate forecasts."""
    
    model_id: UUID = Field(..., description="Model ID")
    horizon: int = Field(..., gt=0, description="Forecast horizon")
    confidence_level: float = Field(0.95, gt=0, lt=1, description="Confidence level for intervals")
    
    @validator("horizon")
    def validate_horizon(cls, v):
        """Validate forecast horizon."""
        from ..core.config import settings
        if v > settings.MAX_FORECAST_HORIZON:
            raise ValueError(f"Horizon exceeds maximum of {settings.MAX_FORECAST_HORIZON}")
        return v


class IdentifyRequest(BaseModel):
    """Request for automatic model identification."""
    
    timeseries: TsDataSchema = Field(..., description="Time series data")
    seasonal: bool = Field(True, description="Consider seasonal models")
    stepwise: bool = Field(True, description="Use stepwise algorithm")
    max_p: int = Field(5, ge=0, le=10, description="Maximum AR order")
    max_q: int = Field(5, ge=0, le=10, description="Maximum MA order")
    max_d: int = Field(2, ge=0, le=3, description="Maximum differencing order")
    information_criterion: Literal["aic", "bic", "aicc"] = Field("aic", description="Information criterion")


class DiagnoseRequest(BaseModel):
    """Request for model diagnostics."""
    
    model_id: UUID = Field(..., description="Model ID")
    tests: List[Literal["ljung_box", "jarque_bera", "heteroscedasticity"]] = Field(
        ["ljung_box", "jarque_bera"],
        description="Diagnostic tests to run"
    )