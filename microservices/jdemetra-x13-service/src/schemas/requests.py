"""Request schemas for X-13 service."""

from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID

from jdemetra_common.schemas import TsDataSchema
from .specification import X13Specification


class ProcessRequest(BaseModel):
    """Request to process time series with X-13."""
    
    timeseries: TsDataSchema = Field(..., description="Time series data")
    specification: Optional[X13Specification] = Field(
        None, 
        description="X-13 specification (uses defaults if not provided)"
    )
    async_processing: bool = Field(
        False,
        description="Process asynchronously (returns job ID)"
    )


class DiagnosticsRequest(BaseModel):
    """Request for diagnostics on results."""
    
    result_id: UUID = Field(..., description="Result ID")
    tests: Optional[List[str]] = Field(
        ["spectrum", "stability", "residuals", "sliding_spans"],
        description="Diagnostic tests to run"
    )


class CompareRequest(BaseModel):
    """Request to compare multiple specifications."""
    
    timeseries: TsDataSchema = Field(..., description="Time series data")
    specifications: List[X13Specification] = Field(
        ...,
        min_items=2,
        max_items=5,
        description="Specifications to compare"
    )
    comparison_criteria: List[Literal["aic", "bic", "ljung_box", "stability"]] = Field(
        ["aic", "ljung_box"],
        description="Criteria for comparison"
    )