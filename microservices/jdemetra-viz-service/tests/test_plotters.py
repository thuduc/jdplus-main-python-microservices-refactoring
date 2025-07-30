"""Tests for plotter implementations."""

import pytest
import os
import numpy as np
from pathlib import Path

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from src.plotters.timeseries import TimeSeriesPlotter
from src.plotters.decomposition import DecompositionPlotter
from src.plotters.spectrum import SpectrumPlotter
from src.plotters.diagnostics import DiagnosticsPlotter
from src.plotters.forecast import ForecastPlotter
from src.schemas.requests import PlotStyle


class TestPlotters:
    """Test individual plotter classes."""
    
    @pytest.fixture
    def sample_ts(self):
        """Create sample time series."""
        return TsData(
            values=list(np.random.normal(100, 10, 50)),
            start_period=TsPeriod(2020, 1, TsFrequency.MONTHLY),
            frequency=TsFrequency.MONTHLY,
            metadata={"name": "Test Series"}
        )
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for plots."""
        return tmp_path
    
    def test_timeseries_plotter(self, sample_ts, temp_dir):
        """Test time series plotter."""
        plotter = TimeSeriesPlotter(PlotStyle(title="Test Plot"))
        output_path = str(temp_dir / "test_ts.png")
        
        result = plotter.plot([sample_ts], output_path)
        
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0
    
    def test_timeseries_plotter_multiple(self, sample_ts, temp_dir):
        """Test plotting multiple series."""
        ts2 = TsData(
            values=list(np.random.normal(150, 15, 50)),
            start_period=TsPeriod(2020, 1, TsFrequency.MONTHLY),
            frequency=TsFrequency.MONTHLY,
            metadata={"name": "Series 2"}
        )
        
        style = PlotStyle(colors=["blue", "red"], legend=True)
        plotter = TimeSeriesPlotter(style)
        output_path = str(temp_dir / "test_multi.png")
        
        result = plotter.plot([sample_ts, ts2], output_path, show_markers=True)
        
        assert os.path.exists(result)
    
    def test_decomposition_plotter(self, sample_ts, temp_dir):
        """Test decomposition plotter."""
        # Create components
        trend = TsData(
            values=list(np.linspace(90, 110, 50)),
            start_period=sample_ts.start_period,
            frequency=sample_ts.frequency,
            metadata={"name": "Trend"}
        )
        
        seasonal = TsData(
            values=list(10 * np.sin(2 * np.pi * np.arange(50) / 12)),
            start_period=sample_ts.start_period,
            frequency=sample_ts.frequency,
            metadata={"name": "Seasonal"}
        )
        
        irregular = TsData(
            values=list(np.random.normal(0, 2, 50)),
            start_period=sample_ts.start_period,
            frequency=sample_ts.frequency,
            metadata={"name": "Irregular"}
        )
        
        plotter = DecompositionPlotter()
        output_path = str(temp_dir / "test_decomp.png")
        
        result = plotter.plot(
            sample_ts, trend, seasonal, irregular,
            output_path,
            method_name="Test Method"
        )
        
        assert os.path.exists(result)
    
    def test_spectrum_plotter(self, temp_dir):
        """Test spectrum plotter."""
        frequencies = list(np.linspace(0, 0.5, 100))
        spectrum = list(1 / (1 + 100 * frequencies**2))
        
        plotter = SpectrumPlotter(PlotStyle(title="Spectrum"))
        output_path = str(temp_dir / "test_spectrum.png")
        
        result = plotter.plot(
            frequencies, spectrum,
            output_path,
            log_scale=True,
            highlight_peaks=True
        )
        
        assert os.path.exists(result)
    
    def test_diagnostics_plotter(self, temp_dir):
        """Test diagnostics plotter."""
        residuals = list(np.random.normal(0, 1, 100))
        
        plotter = DiagnosticsPlotter()
        output_path = str(temp_dir / "test_diag.png")
        
        result = plotter.plot(
            residuals,
            ["acf", "pacf", "qq", "histogram"],
            output_path,
            max_lags=20
        )
        
        assert os.path.exists(result)
    
    def test_forecast_plotter(self, sample_ts, temp_dir):
        """Test forecast plotter."""
        # Create forecast
        forecast = TsData(
            values=list(np.random.normal(105, 12, 12)),
            start_period=TsPeriod(2024, 3, TsFrequency.MONTHLY),
            frequency=TsFrequency.MONTHLY,
            metadata={"name": "Forecast"}
        )
        
        # Create bounds
        lower = TsData(
            values=[v - 20 for v in forecast.values],
            start_period=forecast.start_period,
            frequency=forecast.frequency,
            metadata={"name": "Lower"}
        )
        
        upper = TsData(
            values=[v + 20 for v in forecast.values],
            start_period=forecast.start_period,
            frequency=forecast.frequency,
            metadata={"name": "Upper"}
        )
        
        plotter = ForecastPlotter()
        output_path = str(temp_dir / "test_forecast.png")
        
        result = plotter.plot(
            sample_ts, forecast,
            output_path,
            lower_bound=lower,
            upper_bound=upper,
            show_history_points=24
        )
        
        assert os.path.exists(result)
    
    def test_different_formats(self, sample_ts, temp_dir):
        """Test different output formats."""
        plotter = TimeSeriesPlotter()
        
        formats = ["png", "svg", "pdf"]
        for fmt in formats:
            output_path = str(temp_dir / f"test.{fmt}")
            result = plotter.plot([sample_ts], output_path, format=fmt)
            assert os.path.exists(result)
            assert result.endswith(f".{fmt}")
    
    def test_custom_styling(self, sample_ts, temp_dir):
        """Test custom styling options."""
        style = PlotStyle(
            theme="ggplot",
            figure_size=[12, 8],
            dpi=150,
            title="Custom Styled Plot",
            xlabel="Time",
            ylabel="Values",
            grid=True,
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        plotter = TimeSeriesPlotter(style)
        output_path = str(temp_dir / "test_styled.png")
        
        result = plotter.plot([sample_ts], output_path)
        assert os.path.exists(result)
    
    def test_quarterly_data(self, temp_dir):
        """Test plotting quarterly data."""
        ts = TsData(
            values=list(np.random.normal(100, 10, 20)),
            start_period=TsPeriod(2020, 1, TsFrequency.QUARTERLY),
            frequency=TsFrequency.QUARTERLY,
            metadata={"name": "Quarterly Series"}
        )
        
        plotter = TimeSeriesPlotter()
        output_path = str(temp_dir / "test_quarterly.png")
        
        result = plotter.plot([ts], output_path)
        assert os.path.exists(result)