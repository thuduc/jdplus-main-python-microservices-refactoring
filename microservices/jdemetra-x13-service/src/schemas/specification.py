"""X-13 specification schemas."""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class RegArimaSpec(BaseModel):
    """RegARIMA model specification."""
    
    # ARIMA model
    model: Optional[List[int]] = Field(
        None, 
        min_items=3, 
        max_items=6,
        description="ARIMA model (p d q)(P D Q) or None for automatic"
    )
    
    # Variables
    variables: List[Literal["td", "easter", "ao", "ls", "tc", "user"]] = Field(
        ["td", "easter", "ao", "ls"],
        description="Regression variables"
    )
    
    # Transformation
    transform_function: Literal["auto", "log", "none"] = Field(
        "auto",
        description="Transformation function"
    )
    
    # Outliers
    outlier_critical_value: float = Field(3.0, gt=0, description="Critical value for outlier detection")
    outlier_method: Literal["addone", "addall"] = Field("addone", description="Outlier detection method")


class X11Spec(BaseModel):
    """X-11 decomposition specification."""
    
    mode: Literal["add", "mult", "logadd", "pseudoadd"] = Field(
        "mult",
        description="Decomposition mode"
    )
    
    seasonalma: Optional[List[int]] = Field(
        None,
        description="Seasonal moving average filter"
    )
    
    trendma: Optional[int] = Field(
        None,
        description="Trend moving average length"
    )
    
    sigmalim: List[float] = Field(
        [1.5, 2.5],
        min_items=2,
        max_items=2,
        description="Sigma limits for extreme value detection"
    )


class SeatsSpec(BaseModel):
    """SEATS decomposition specification (alternative to X-11)."""
    
    noadmiss: bool = Field(False, description="Reject non-admissible models")
    
    xl_boundary: float = Field(0.95, gt=0, lt=1, description="MA root boundary")
    
    rmod: float = Field(0.5, gt=0, lt=1, description="Trend MA root mod limit")
    
    smod: float = Field(0.8, gt=0, lt=1, description="Seasonal MA root mod limit")


class X13Specification(BaseModel):
    """Complete X-13 specification."""
    
    series_span: Optional[List[str]] = Field(
        None,
        min_items=2,
        max_items=2,
        description="Series span [start, end] in format 'YYYY.M'"
    )
    
    regarima: RegArimaSpec = Field(
        default_factory=RegArimaSpec,
        description="RegARIMA specification"
    )
    
    x11: Optional[X11Spec] = Field(
        default_factory=X11Spec,
        description="X-11 specification (if using X-11)"
    )
    
    seats: Optional[SeatsSpec] = Field(
        None,
        description="SEATS specification (if using SEATS instead of X-11)"
    )
    
    forecast_maxlead: int = Field(
        12,
        gt=0,
        le=60,
        description="Maximum forecast lead"
    )
    
    check_maxlag: int = Field(
        24,
        gt=0,
        description="Maximum lag for diagnostic checking"
    )