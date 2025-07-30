"""Request schemas for I/O service."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from uuid import UUID


class ImportRequest(BaseModel):
    """Request for data import."""
    
    file_id: str = Field(..., description="Uploaded file ID")
    format: Literal["csv", "excel", "json", "xml", "yaml"] = Field(..., description="File format")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Format-specific options"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "file_id": "data_2024_01.csv",
                "format": "csv",
                "options": {
                    "delimiter": ",",
                    "header": True,
                    "date_column": 0,
                    "value_columns": [1, 2, 3]
                }
            }
        }


class ExportRequest(BaseModel):
    """Request for data export."""
    
    series_ids: List[UUID] = Field(..., description="Time series IDs to export")
    format: Literal["csv", "excel", "json", "xml", "yaml"] = Field(..., description="Export format")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Format-specific options"
    )
    filename: Optional[str] = Field(None, description="Output filename")
    
    @validator("series_ids")
    def validate_series_count(cls, v):
        if len(v) > 1000:
            raise ValueError("Cannot export more than 1000 series at once")
        return v


class ConvertRequest(BaseModel):
    """Request for format conversion."""
    
    source_file_id: str = Field(..., description="Source file ID")
    source_format: Literal["csv", "excel", "json", "xml", "yaml"] = Field(..., description="Source format")
    target_format: Literal["csv", "excel", "json", "xml", "yaml"] = Field(..., description="Target format")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Conversion options"
    )
    
    @validator("target_format")
    def validate_different_formats(cls, v, values):
        if "source_format" in values and v == values["source_format"]:
            raise ValueError("Source and target formats must be different")
        return v


class ValidateRequest(BaseModel):
    """Request for file validation."""
    
    file_id: str = Field(..., description="File ID to validate")
    format: Literal["csv", "excel", "json", "xml", "yaml"] = Field(..., description="Expected format")
    strict: bool = Field(False, description="Strict validation mode")