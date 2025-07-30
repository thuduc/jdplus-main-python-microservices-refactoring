"""Visualization API endpoints."""

import os
import time
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from uuid import uuid4

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from ..schemas.requests import (
    TimeSeriesPlotRequest, DecompositionPlotRequest,
    SpectrumPlotRequest, DiagnosticsPlotRequest,
    ForecastPlotRequest, ComparisonPlotRequest,
    BatchPlotRequest
)
from ..schemas.responses import (
    PlotResponse, BatchPlotResponse, 
    ThemesResponse, ThemeInfo
)
from ..plotters.timeseries import TimeSeriesPlotter
from ..plotters.decomposition import DecompositionPlotter
from ..plotters.spectrum import SpectrumPlotter
from ..plotters.diagnostics import DiagnosticsPlotter
from ..plotters.forecast import ForecastPlotter
from ..core.cache import plot_cache
from ..core.config import settings

router = APIRouter()


@router.post("/viz/timeseries", response_model=PlotResponse)
async def plot_timeseries(request: TimeSeriesPlotRequest):
    """Generate time series plot."""
    try:
        # Check cache
        cache_key = {"type": "timeseries", "params": request.dict()}
        cached_path = await plot_cache.get("timeseries", cache_key)
        
        if cached_path and os.path.exists(cached_path):
            # Return cached plot
            file_size = os.path.getsize(cached_path)
            return PlotResponse(
                plot_id=Path(cached_path).stem,
                download_url=f"/api/v1/viz/download/{Path(cached_path).name}",
                format=request.format,
                size_bytes=file_size,
                dimensions={"width": 1000, "height": 600},
                created_at=time.time(),
                cache_hit=True
            )
        
        # Convert schemas to TsData
        series_list = []
        for ts_schema in request.series:
            ts = TsData(
                values=ts_schema.values,
                start_period=TsPeriod(
                    year=ts_schema.start_period.year,
                    period=ts_schema.start_period.period,
                    frequency=ts_schema.start_period.frequency
                ),
                frequency=ts_schema.frequency,
                metadata=ts_schema.metadata
            )
            series_list.append(ts)
        
        # Generate plot
        plot_id = plot_cache.generate_plot_id()
        output_path = f"{settings.PLOT_CACHE_DIR}/{plot_id}.{request.format}"
        
        plotter = TimeSeriesPlotter(request.style)
        plotter.plot(
            series_list,
            output_path,
            format=request.format,
            date_format=request.date_format,
            show_markers=request.show_markers,
            annotations=request.annotations
        )
        
        # Cache the result
        await plot_cache.set("timeseries", cache_key, output_path)
        
        # Get file info
        file_size = os.path.getsize(output_path)
        
        return PlotResponse(
            plot_id=plot_id,
            download_url=f"/api/v1/viz/download/{plot_id}.{request.format}",
            format=request.format,
            size_bytes=file_size,
            dimensions={"width": 1000, "height": 600},
            created_at=time.time(),
            cache_hit=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/viz/decomposition", response_model=PlotResponse)
async def plot_decomposition(request: DecompositionPlotRequest):
    """Generate decomposition plot."""
    try:
        # Convert schemas to TsData
        def schema_to_tsdata(schema):
            return TsData(
                values=schema.values,
                start_period=TsPeriod(
                    year=schema.start_period.year,
                    period=schema.start_period.period,
                    frequency=schema.start_period.frequency
                ),
                frequency=schema.frequency,
                metadata=schema.metadata
            )
        
        original = schema_to_tsdata(request.original)
        trend = schema_to_tsdata(request.trend)
        seasonal = schema_to_tsdata(request.seasonal)
        irregular = schema_to_tsdata(request.irregular)
        
        # Generate plot
        plot_id = plot_cache.generate_plot_id()
        output_path = f"{settings.PLOT_CACHE_DIR}/{plot_id}.{request.format}"
        
        plotter = DecompositionPlotter(request.style)
        plotter.plot(
            original, trend, seasonal, irregular,
            output_path,
            format=request.format,
            method_name=request.method_name
        )
        
        # Get file info
        file_size = os.path.getsize(output_path)
        
        return PlotResponse(
            plot_id=plot_id,
            download_url=f"/api/v1/viz/download/{plot_id}.{request.format}",
            format=request.format,
            size_bytes=file_size,
            dimensions={"width": 1000, "height": 800},
            created_at=time.time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/viz/spectrum", response_model=PlotResponse)
async def plot_spectrum(request: SpectrumPlotRequest):
    """Generate spectrum plot."""
    try:
        # Generate plot
        plot_id = plot_cache.generate_plot_id()
        output_path = f"{settings.PLOT_CACHE_DIR}/{plot_id}.{request.format}"
        
        plotter = SpectrumPlotter(request.style)
        plotter.plot(
            request.frequencies,
            request.spectrum,
            output_path,
            format=request.format,
            log_scale=request.log_scale,
            highlight_peaks=request.highlight_peaks,
            peak_threshold=request.peak_threshold
        )
        
        # Get file info
        file_size = os.path.getsize(output_path)
        
        return PlotResponse(
            plot_id=plot_id,
            download_url=f"/api/v1/viz/download/{plot_id}.{request.format}",
            format=request.format,
            size_bytes=file_size,
            dimensions={"width": 1000, "height": 600},
            created_at=time.time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/viz/diagnostics", response_model=PlotResponse)
async def plot_diagnostics(request: DiagnosticsPlotRequest):
    """Generate diagnostic plots."""
    try:
        # Generate plot
        plot_id = plot_cache.generate_plot_id()
        output_path = f"{settings.PLOT_CACHE_DIR}/{plot_id}.{request.format}"
        
        plotter = DiagnosticsPlotter(request.style)
        plotter.plot(
            request.residuals,
            request.plot_types,
            output_path,
            format=request.format,
            max_lags=request.max_lags,
            confidence_level=request.confidence_level
        )
        
        # Get file info
        file_size = os.path.getsize(output_path)
        
        return PlotResponse(
            plot_id=plot_id,
            download_url=f"/api/v1/viz/download/{plot_id}.{request.format}",
            format=request.format,
            size_bytes=file_size,
            dimensions={"width": 1000, "height": 800},
            created_at=time.time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/viz/forecast", response_model=PlotResponse)
async def plot_forecast(request: ForecastPlotRequest):
    """Generate forecast plot."""
    try:
        # Convert schemas to TsData
        def schema_to_tsdata(schema):
            return TsData(
                values=schema.values,
                start_period=TsPeriod(
                    year=schema.start_period.year,
                    period=schema.start_period.period,
                    frequency=schema.start_period.frequency
                ),
                frequency=schema.frequency,
                metadata=schema.metadata
            )
        
        historical = schema_to_tsdata(request.historical)
        forecast = schema_to_tsdata(request.forecast)
        lower_bound = schema_to_tsdata(request.lower_bound) if request.lower_bound else None
        upper_bound = schema_to_tsdata(request.upper_bound) if request.upper_bound else None
        
        # Generate plot
        plot_id = plot_cache.generate_plot_id()
        output_path = f"{settings.PLOT_CACHE_DIR}/{plot_id}.{request.format}"
        
        plotter = ForecastPlotter(request.style)
        plotter.plot(
            historical, forecast,
            output_path,
            format=request.format,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            show_history_points=request.show_history_points,
            confidence_level=request.confidence_level
        )
        
        # Get file info
        file_size = os.path.getsize(output_path)
        
        return PlotResponse(
            plot_id=plot_id,
            download_url=f"/api/v1/viz/download/{plot_id}.{request.format}",
            format=request.format,
            size_bytes=file_size,
            dimensions={"width": 1000, "height": 600},
            created_at=time.time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/viz/themes", response_model=ThemesResponse)
async def list_themes():
    """List available plot themes."""
    themes = []
    
    for theme_name in settings.AVAILABLE_THEMES:
        themes.append(ThemeInfo(
            name=theme_name,
            description=f"Matplotlib {theme_name} theme",
            is_default=(theme_name == settings.DEFAULT_THEME)
        ))
    
    return ThemesResponse(
        themes=themes,
        current_default=settings.DEFAULT_THEME
    )


@router.get("/viz/download/{file_name}")
async def download_plot(file_name: str):
    """Download generated plot."""
    file_path = f"{settings.PLOT_CACHE_DIR}/{file_name}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Plot not found")
    
    # Determine content type
    ext = Path(file_name).suffix.lower()
    content_types = {
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.pdf': 'application/pdf',
        '.html': 'text/html'
    }
    
    media_type = content_types.get(ext, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_name
    )