"""Pydantic schemas for ARIMA models."""

from typing import Optional, List
from pydantic import BaseModel, Field, validator


class ArimaOrderSchema(BaseModel):
    """Schema for ARIMA order specification."""
    
    p: int = Field(..., ge=0, description="AR order")
    d: int = Field(..., ge=0, description="Differencing order")
    q: int = Field(..., ge=0, description="MA order")
    seasonal_p: int = Field(0, ge=0, description="Seasonal AR order")
    seasonal_d: int = Field(0, ge=0, description="Seasonal differencing order")
    seasonal_q: int = Field(0, ge=0, description="Seasonal MA order")
    seasonal_period: int = Field(0, ge=0, description="Seasonal period")
    
    @validator("seasonal_period")
    def validate_seasonal_period(cls, v, values):
        """Validate seasonal period consistency."""
        has_seasonal = any([
            values.get("seasonal_p", 0) > 0,
            values.get("seasonal_d", 0) > 0,
            values.get("seasonal_q", 0) > 0
        ])
        if has_seasonal and v == 0:
            raise ValueError("Seasonal period must be > 0 when seasonal components are specified")
        return v


class ArimaModelSchema(BaseModel):
    """Schema for estimated ARIMA model."""
    
    order: ArimaOrderSchema = Field(..., description="Model order")
    ar_params: Optional[List[float]] = Field(None, description="AR parameters")
    ma_params: Optional[List[float]] = Field(None, description="MA parameters")
    seasonal_ar_params: Optional[List[float]] = Field(None, description="Seasonal AR parameters")
    seasonal_ma_params: Optional[List[float]] = Field(None, description="Seasonal MA parameters")
    intercept: float = Field(0.0, description="Model intercept")
    sigma2: float = Field(1.0, gt=0, description="Residual variance")
    log_likelihood: Optional[float] = Field(None, description="Log-likelihood")
    aic: Optional[float] = Field(None, description="Akaike Information Criterion")
    bic: Optional[float] = Field(None, description="Bayesian Information Criterion")