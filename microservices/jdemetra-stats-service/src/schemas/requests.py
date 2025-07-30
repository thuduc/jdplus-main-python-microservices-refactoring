"""Request schemas for statistical analysis."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


class StatisticalDataRequest(BaseModel):
    """Base request with data."""
    data: List[float] = Field(..., description="Data values")
    
    @validator("data")
    def validate_data(cls, v):
        if not v:
            raise ValueError("Data cannot be empty")
        return v


class NormalityTestRequest(StatisticalDataRequest):
    """Request for normality test."""
    method: Literal["shapiro", "jarque_bera", "anderson"] = Field(
        "shapiro",
        description="Test method"
    )


class StationarityTestRequest(StatisticalDataRequest):
    """Request for stationarity test."""
    method: Literal["adf", "kpss", "pp"] = Field(
        "adf",
        description="Test method (ADF, KPSS, Phillips-Perron)"
    )
    regression: Literal["c", "ct", "ctt", "n"] = Field(
        "c",
        description="Regression type: c=constant, ct=constant+trend, ctt=constant+trend+trend², n=none"
    )
    max_lag: Optional[int] = Field(None, description="Maximum lag to consider")


class DescriptiveStatsRequest(StatisticalDataRequest):
    """Request for descriptive statistics."""
    percentiles: Optional[List[float]] = Field(
        [25, 50, 75],
        description="Percentiles to compute"
    )


class DistributionFitRequest(StatisticalDataRequest):
    """Request for distribution fitting."""
    distributions: List[Literal["normal", "lognormal", "exponential", "gamma", "beta"]] = Field(
        ["normal"],
        description="Distributions to fit"
    )


class RandomnessTestRequest(StatisticalDataRequest):
    """Request for randomness test."""
    method: Literal["runs", "ljung_box", "box_pierce"] = Field(
        "runs",
        description="Test method"
    )
    lags: Optional[int] = Field(10, description="Number of lags for Ljung-Box/Box-Pierce")


class SeasonalityTestRequest(StatisticalDataRequest):
    """Request for seasonality test."""
    period: int = Field(..., gt=1, description="Seasonal period")
    method: Literal["kruskal", "friedman", "qs", "auto"] = Field(
        "auto",
        description="Test method"
    )