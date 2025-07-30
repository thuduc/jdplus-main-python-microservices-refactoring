"""Response schemas for I/O service."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from jdemetra_common.schemas import TsDataSchema


class ImportedSeries(BaseModel):
    """Single imported time series."""
    
    series_id: UUID = Field(..., description="Assigned series ID")
    name: Optional[str] = Field(None, description="Series name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Series metadata")


class ImportResponse(BaseModel):
    """Import response."""
    
    import_id: UUID = Field(..., description="Import job ID")
    status: str = Field(..., description="Import status")
    imported_series: List[ImportedSeries] = Field(..., description="List of imported series")
    total_series: int = Field(..., description="Total number of series imported")
    warnings: List[str] = Field(default_factory=list, description="Import warnings")
    import_time: float = Field(..., description="Import time in seconds")


class ExportResponse(BaseModel):
    """Export response."""
    
    export_id: UUID = Field(..., description="Export job ID")
    file_id: str = Field(..., description="Exported file ID")
    download_url: str = Field(..., description="Download URL")
    format: str = Field(..., description="Export format")
    file_size: int = Field(..., description="File size in bytes")
    expires_at: datetime = Field(..., description="Download expiration time")


class ConvertResponse(BaseModel):
    """Format conversion response."""
    
    conversion_id: UUID = Field(..., description="Conversion job ID")
    source_file: str = Field(..., description="Source file ID")
    target_file: str = Field(..., description="Target file ID")
    download_url: str = Field(..., description="Download URL for converted file")
    conversion_time: float = Field(..., description="Conversion time in seconds")


class ValidationResult(BaseModel):
    """File validation result."""
    
    valid: bool = Field(..., description="Whether file is valid")
    format_detected: Optional[str] = Field(None, description="Detected format")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    file_info: Dict[str, Any] = Field(..., description="File information")


class FormatInfo(BaseModel):
    """Information about a supported format."""
    
    format: str = Field(..., description="Format identifier")
    name: str = Field(..., description="Format name")
    extensions: List[str] = Field(..., description="File extensions")
    supports_import: bool = Field(..., description="Supports import")
    supports_export: bool = Field(..., description="Supports export")
    options: Dict[str, Any] = Field(..., description="Available options")


class FormatsResponse(BaseModel):
    """List of supported formats."""
    
    formats: List[FormatInfo] = Field(..., description="Supported formats")