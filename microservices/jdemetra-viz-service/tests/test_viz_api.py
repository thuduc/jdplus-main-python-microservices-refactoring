"""Tests for visualization API."""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from src.main import app


class TestVisualizationAPI:
    """Test visualization API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_timeseries(self):
        """Generate sample time series."""
        return {
            "values": list(np.random.normal(100, 10, 50)),
            "start_period": {"year": 2020, "period": 1, "frequency": "M"},
            "frequency": "M",
            "metadata": {"name": "Test Series"}
        }
    
    def test_plot_timeseries(self, client, sample_timeseries):
        """Test time series plotting."""
        request = {
            "series": [sample_timeseries],
            "format": "png",
            "style": {
                "title": "Test Time Series Plot",
                "xlabel": "Date",
                "ylabel": "Value"
            }
        }
        
        response = client.post("/api/v1/viz/timeseries", json=request)
        assert response.status_code == 200
        
        result = response.json()
        assert "plot_id" in result
        assert "download_url" in result
        assert result["format"] == "png"
        assert result["size_bytes"] > 0
    
    def test_plot_multiple_series(self, client, sample_timeseries):
        """Test plotting multiple series."""
        series2 = sample_timeseries.copy()
        series2["values"] = list(np.random.normal(150, 15, 50))
        series2["metadata"]["name"] = "Series 2"
        
        request = {
            "series": [sample_timeseries, series2],
            "format": "svg",
            "show_markers": True
        }
        
        response = client.post("/api/v1/viz/timeseries", json=request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["format"] == "svg"
    
    def test_plot_decomposition(self, client, sample_timeseries):
        """Test decomposition plotting."""
        # Create decomposition components
        trend = sample_timeseries.copy()
        trend["values"] = list(np.linspace(90, 110, 50))
        
        seasonal = sample_timeseries.copy()
        seasonal["values"] = list(10 * np.sin(2 * np.pi * np.arange(50) / 12))
        
        irregular = sample_timeseries.copy()
        irregular["values"] = list(np.random.normal(0, 2, 50))
        
        request = {
            "original": sample_timeseries,
            "trend": trend,
            "seasonal": seasonal,
            "irregular": irregular,
            "format": "png",
            "method_name": "Test Decomposition"
        }
        
        response = client.post("/api/v1/viz/decomposition", json=request)
        assert response.status_code == 200
        
        result = response.json()
        assert "plot_id" in result
        assert result["dimensions"]["height"] == 800  # Multi-panel plot
    
    def test_plot_spectrum(self, client):
        """Test spectrum plotting."""
        # Generate sample spectrum
        frequencies = list(np.linspace(0, 0.5, 100))
        spectrum = list(1 / (1 + 100 * frequencies**2))  # Simple spectrum
        
        request = {
            "frequencies": frequencies,
            "spectrum": spectrum,
            "format": "png",
            "log_scale": True,
            "highlight_peaks": True
        }
        
        response = client.post("/api/v1/viz/spectrum", json=request)
        assert response.status_code == 200
        
        result = response.json()
        assert "plot_id" in result
    
    def test_plot_diagnostics(self, client):
        """Test diagnostic plots."""
        # Generate sample residuals
        residuals = list(np.random.normal(0, 1, 100))
        
        request = {
            "residuals": residuals,
            "plot_types": ["acf", "pacf", "qq", "histogram"],
            "format": "png",
            "max_lags": 20
        }
        
        response = client.post("/api/v1/viz/diagnostics", json=request)
        assert response.status_code == 200
        
        result = response.json()
        assert "plot_id" in result
    
    def test_plot_forecast(self, client, sample_timeseries):
        """Test forecast plotting."""
        # Historical data
        historical = sample_timeseries.copy()
        
        # Forecast data
        forecast = {
            "values": list(np.random.normal(105, 12, 12)),
            "start_period": {"year": 2024, "period": 3, "frequency": "M"},
            "frequency": "M",
            "metadata": {"name": "Forecast"}
        }
        
        # Confidence bounds
        lower = forecast.copy()
        lower["values"] = [v - 20 for v in forecast["values"]]
        
        upper = forecast.copy()
        upper["values"] = [v + 20 for v in forecast["values"]]
        
        request = {
            "historical": historical,
            "forecast": forecast,
            "lower_bound": lower,
            "upper_bound": upper,
            "format": "png",
            "show_history_points": 24
        }
        
        response = client.post("/api/v1/viz/forecast", json=request)
        assert response.status_code == 200
        
        result = response.json()
        assert "plot_id" in result
    
    def test_list_themes(self, client):
        """Test theme listing."""
        response = client.get("/api/v1/viz/themes")
        assert response.status_code == 200
        
        result = response.json()
        assert "themes" in result
        assert len(result["themes"]) > 0
        assert any(t["is_default"] for t in result["themes"])
    
    def test_download_plot(self, client, sample_timeseries):
        """Test plot download."""
        # First create a plot
        request = {
            "series": [sample_timeseries],
            "format": "png"
        }
        
        create_response = client.post("/api/v1/viz/timeseries", json=request)
        plot_result = create_response.json()
        
        # Extract filename from download URL
        filename = plot_result["download_url"].split("/")[-1]
        
        # Download the plot
        download_response = client.get(f"/api/v1/viz/download/{filename}")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "image/png"
    
    def test_plot_caching(self, client, sample_timeseries):
        """Test plot caching."""
        request = {
            "series": [sample_timeseries],
            "format": "png"
        }
        
        # First request
        response1 = client.post("/api/v1/viz/timeseries", json=request)
        result1 = response1.json()
        assert not result1["cache_hit"]
        
        # Second identical request should hit cache
        response2 = client.post("/api/v1/viz/timeseries", json=request)
        result2 = response2.json()
        assert result2["cache_hit"]
        assert result2["plot_id"] == result1["plot_id"]
    
    def test_invalid_format(self, client, sample_timeseries):
        """Test invalid format handling."""
        request = {
            "series": [sample_timeseries],
            "format": "invalid"
        }
        
        response = client.post("/api/v1/viz/timeseries", json=request)
        assert response.status_code == 422  # Validation error
    
    def test_plot_with_annotations(self, client, sample_timeseries):
        """Test plot with annotations."""
        request = {
            "series": [sample_timeseries],
            "format": "png",
            "annotations": [
                {
                    "date": "2021-01-01",
                    "text": "Important Event",
                    "y": 100
                }
            ]
        }
        
        response = client.post("/api/v1/viz/timeseries", json=request)
        assert response.status_code == 200