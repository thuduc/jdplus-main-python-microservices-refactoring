"""Request schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from jdemetra_common.schemas import TimeSeriesSchema


class PlotStyle(BaseModel):
    """Plot styling options."""
    theme: Optional[str] = None
    figure_size: Optional[List[float]] = Field(None, min_items=2, max_items=2)
    dpi: Optional[int] = Field(None, ge=50, le=300)
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    grid: Optional[bool] = True
    legend: Optional[bool] = True
    colors: Optional[List[str]] = None
    line_style: Optional[str] = None
    marker_style: Optional[str] = None


class TimeSeriesPlotRequest(BaseModel):
    """Request for time series plot."""
    series: List[TimeSeriesSchema]
    format: str = Field("png", pattern="^(png|svg|pdf|html)$")
    style: Optional[PlotStyle] = None
    date_format: Optional[str] = "%Y-%m"
    show_markers: bool = False
    annotations: Optional[List[Dict[str, Any]]] = None


class DecompositionPlotRequest(BaseModel):
    """Request for decomposition plot."""
    original: TimeSeriesSchema
    trend: TimeSeriesSchema
    seasonal: TimeSeriesSchema
    irregular: TimeSeriesSchema
    format: str = Field("png", pattern="^(png|svg|pdf|html)$")
    style: Optional[PlotStyle] = None
    method_name: Optional[str] = "Decomposition"


class SpectrumPlotRequest(BaseModel):
    """Request for spectrum plot."""
    frequencies: List[float]
    spectrum: List[float]
    format: str = Field("png", pattern="^(png|svg|pdf|html)$")
    style: Optional[PlotStyle] = None
    log_scale: bool = True
    highlight_peaks: bool = True
    peak_threshold: Optional[float] = None


class DiagnosticsPlotRequest(BaseModel):
    """Request for diagnostic plots."""
    residuals: List[float]
    plot_types: List[str] = Field(
        default=["acf", "pacf", "qq", "histogram"],
        description="Types: acf, pacf, qq, histogram, residuals"
    )
    format: str = Field("png", pattern="^(png|svg|pdf|html)$")
    style: Optional[PlotStyle] = None
    max_lags: Optional[int] = 40
    confidence_level: float = 0.95


class ForecastPlotRequest(BaseModel):
    """Request for forecast plot."""
    historical: TimeSeriesSchema
    forecast: TimeSeriesSchema
    lower_bound: Optional[TimeSeriesSchema] = None
    upper_bound: Optional[TimeSeriesSchema] = None
    format: str = Field("png", pattern="^(png|svg|pdf|html)$")
    style: Optional[PlotStyle] = None
    show_history_points: int = Field(50, description="Number of historical points to show")
    confidence_level: Optional[float] = 0.95


class ComparisonPlotRequest(BaseModel):
    """Request for comparison plot."""
    series: List[TimeSeriesSchema]
    plot_type: str = Field("line", pattern="^(line|bar|scatter|box)$")
    format: str = Field("png", pattern="^(png|svg|pdf|html)$")
    style: Optional[PlotStyle] = None
    normalize: bool = False
    show_differences: bool = False


class BatchPlotRequest(BaseModel):
    """Request for batch plot generation."""
    plots: List[Dict[str, Any]]  # List of plot requests
    output_format: str = Field("png", pattern="^(png|svg|pdf|html)$")
    combine_pdf: bool = Field(False, description="Combine into single PDF")
    style: Optional[PlotStyle] = None