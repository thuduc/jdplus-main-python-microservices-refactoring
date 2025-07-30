"""Response schemas for statistical analysis."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """Generic test result."""
    statistic: float = Field(..., description="Test statistic")
    p_value: float = Field(..., description="P-value")
    reject_null: bool = Field(..., description="Whether to reject null hypothesis at 5% level")
    interpretation: str = Field(..., description="Human-readable interpretation")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional test-specific information")


class DescriptiveStatsResponse(BaseModel):
    """Descriptive statistics response."""
    count: int = Field(..., description="Number of observations")
    mean: float = Field(..., description="Mean")
    std: float = Field(..., description="Standard deviation")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    percentiles: Dict[str, float] = Field(..., description="Requested percentiles")
    skewness: float = Field(..., description="Skewness")
    kurtosis: float = Field(..., description="Kurtosis")
    variance: float = Field(..., description="Variance")
    coefficient_of_variation: Optional[float] = Field(None, description="CV (std/mean)")


class DistributionFitResponse(BaseModel):
    """Distribution fitting result."""
    distribution: str = Field(..., description="Distribution name")
    parameters: Dict[str, float] = Field(..., description="Fitted parameters")
    goodness_of_fit: Dict[str, float] = Field(..., description="Goodness of fit metrics (KS test, AIC, BIC)")
    best_fit: bool = Field(..., description="Whether this is the best fit among tested")


class DistributionFitListResponse(BaseModel):
    """List of distribution fitting results."""
    results: List[DistributionFitResponse] = Field(..., description="Fitting results for each distribution")
    best_distribution: str = Field(..., description="Best fitting distribution")