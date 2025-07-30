"""Request schemas for TRAMO/SEATS service."""

from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID

from jdemetra_common.schemas import TsDataSchema
from .specification import TramoSeatsSpecification


class ProcessRequest(BaseModel):
    """Request to process time series with TRAMO/SEATS."""
    
    timeseries: TsDataSchema = Field(..., description="Time series data")
    specification: Optional[TramoSeatsSpecification] = Field(
        None, 
        description="TRAMO/SEATS specification (uses defaults if not provided)"
    )
    async_processing: bool = Field(
        False,
        description="Process asynchronously (returns job ID)"
    )


class DiagnosticsRequest(BaseModel):
    """Request for diagnostics on results."""
    
    result_id: UUID = Field(..., description="Result ID")
    tests: Optional[list[str]] = Field(
        ["seasonality", "residuals", "spectral"],
        description="Diagnostic tests to run"
    )