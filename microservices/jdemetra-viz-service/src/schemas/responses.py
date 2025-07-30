"""Response schemas."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class PlotResponse(BaseModel):
    """Response for plot generation."""
    plot_id: str
    download_url: str
    format: str
    size_bytes: int
    dimensions: Dict[str, int]  # width, height
    created_at: datetime
    cache_hit: bool = False


class BatchPlotResponse(BaseModel):
    """Response for batch plot generation."""
    batch_id: str
    plots: List[PlotResponse]
    total_plots: int
    combined_pdf_url: Optional[str] = None
    processing_time: float


class ThemeInfo(BaseModel):
    """Theme information."""
    name: str
    description: str
    preview_url: Optional[str] = None
    is_default: bool = False


class ThemesResponse(BaseModel):
    """Response for available themes."""
    themes: List[ThemeInfo]
    current_default: str


class PlotError(BaseModel):
    """Plot generation error."""
    error: str
    details: Optional[str] = None
    plot_type: Optional[str] = None