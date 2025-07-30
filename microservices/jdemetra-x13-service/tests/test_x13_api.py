"""Tests for X-13 API."""

import pytest
import numpy as np
import pickle
from uuid import UUID
from fastapi.testclient import TestClient

# Mock Redis
class MockRedis:
    def __init__(self):
        self.data = {}
    
    async def setex(self, key, ttl, value):
        self.data[key] = value
    
    async def get(self, key):
        return self.data.get(key)

# Override dependencies
from src.main import app, get_redis
mock_redis = MockRedis()
app.dependency_overrides[get_redis] = lambda: mock_redis


class TestX13API:
    """Test X-13 API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_timeseries(self):
        """Generate sample seasonal time series."""
        np.random.seed(42)
        n = 120  # 10 years monthly
        trend = np.linspace(100, 120, n)
        seasonal = 10 * np.sin(2 * np.pi * np.arange(n) / 12)
        irregular = np.random.normal(0, 2, n)
        values = trend + seasonal + irregular
        
        return {
            "timeseries": {
                "values": values.tolist(),
                "start_period": {"year": 2014, "period": 1, "frequency": "M"},
                "frequency": "M",
                "metadata": {"name": "Test seasonal series"}
            }
        }
    
    def test_process_default(self, client, sample_timeseries):
        """Test processing with default specification."""
        response = client.post(
            "/api/v1/x13/process",
            json=sample_timeseries
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "result_id" in result
        assert UUID(result["result_id"])
        assert result["status"] == "completed"
        
        # Check RegARIMA results
        assert "regarima_results" in result
        regarima = result["regarima_results"]
        assert "model" in regarima
        assert "outliers" in regarima
        assert "transformation" in regarima
        
        # Check decomposition results (should have X-11 by default)
        assert "x11_results" in result
        x11 = result["x11_results"]
        assert "d10" in x11  # Seasonal factors
        assert "d11" in x11  # Seasonally adjusted
        assert "d12" in x11  # Trend
        assert "d13" in x11  # Irregular
    
    def test_process_with_seats(self, client, sample_timeseries):
        """Test processing with SEATS decomposition."""
        request = sample_timeseries.copy()
        request["specification"] = {
            "regarima": {
                "model": [1, 1, 1, 0, 1, 1],  # (1,1,1)(0,1,1)
                "variables": ["td", "easter", "ao", "ls"],
                "transform_function": "log"
            },
            "seats": {
                "noadmiss": False,
                "xl_boundary": 0.95,
                "rmod": 0.5,
                "smod": 0.8
            }
        }
        
        response = client.post(
            "/api/v1/x13/process",
            json=request
        )
        assert response.status_code == 200
        
        result = response.json()
        # Should have SEATS results instead of X-11
        assert "seats_results" in result
        assert "x11_results" not in result
        
        seats = result["seats_results"]
        assert "trend" in seats
        assert "seasonal" in seats
        assert "irregular" in seats
        assert "seasonally_adjusted" in seats
    
    def test_get_results(self, client, sample_timeseries):
        """Test retrieving results."""
        # First process
        process_response = client.post(
            "/api/v1/x13/process",
            json=sample_timeseries
        )
        result_id = process_response.json()["result_id"]
        
        # Then retrieve
        response = client.get(f"/api/v1/x13/results/{result_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert result["result_id"] == result_id
        assert "regarima_results" in result
    
    def test_create_specification(self, client):
        """Test specification creation."""
        specification = {
            "series_span": ["2020.1", "2023.12"],
            "regarima": {
                "model": [0, 1, 1, 0, 1, 1],
                "variables": ["td", "easter"],
                "transform_function": "auto",
                "outlier_critical_value": 4.0
            },
            "x11": {
                "mode": "mult",
                "sigmalim": [1.5, 2.5]
            },
            "forecast_maxlead": 24
        }
        
        response = client.post(
            "/api/v1/x13/specification",
            json=specification
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "specification_id" in result
        assert result["valid"] is True
    
    def test_diagnostics(self, client, sample_timeseries):
        """Test diagnostics."""
        # First process
        process_response = client.post(
            "/api/v1/x13/process",
            json=sample_timeseries
        )
        result_id = process_response.json()["result_id"]
        
        # Run diagnostics
        diag_request = {
            "result_id": result_id,
            "tests": ["spectrum", "stability", "residuals", "sliding_spans"]
        }
        
        response = client.post(
            "/api/v1/x13/diagnostics",
            json=diag_request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["result_id"] == result_id
        assert "summary_statistics" in result
        
        # Check diagnostic tests
        assert "spectrum_analysis" in result
        assert "stability_tests" in result
        assert "residual_diagnostics" in result
        assert "sliding_spans" in result
    
    def test_compare_specifications(self, client, sample_timeseries):
        """Test specification comparison."""
        request = {
            "timeseries": sample_timeseries["timeseries"],
            "specifications": [
                {
                    "regarima": {"model": None, "transform_function": "log"},
                    "x11": {"mode": "mult"}
                },
                {
                    "regarima": {"model": [1, 1, 1], "transform_function": "none"},
                    "x11": {"mode": "add"}
                },
                {
                    "regarima": {"model": [0, 1, 1, 0, 1, 1]},
                    "seats": {}
                }
            ],
            "comparison_criteria": ["aic", "ljung_box", "stability"]
        }
        
        response = client.post(
            "/api/v1/x13/compare",
            json=request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "comparison_id" in result
        assert "results" in result
        assert len(result["results"]) == 3
        
        # Check comparison results
        for comp_result in result["results"]:
            assert "specification_index" in comp_result
            assert "aic" in comp_result
            assert "ljung_box_pvalue" in comp_result
            assert "rank" in comp_result
        
        assert "best_specification_index" in result
        assert result["best_specification_index"] in [0, 1, 2]
    
    def test_async_processing(self, client, sample_timeseries):
        """Test async processing request."""
        request = sample_timeseries.copy()
        request["async_processing"] = True
        
        response = client.post(
            "/api/v1/x13/process",
            json=request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "job_id" in result
        assert result["status"] == "pending"
    
    def test_outlier_detection(self, client):
        """Test outlier detection in processing."""
        # Create series with outliers
        np.random.seed(42)
        values = list(np.random.normal(100, 5, 100))
        values[20] = 150  # Add outlier
        values[50] = 50   # Add another outlier
        
        request = {
            "timeseries": {
                "values": values,
                "start_period": {"year": 2020, "period": 1, "frequency": "M"},
                "frequency": "M"
            },
            "specification": {
                "regarima": {
                    "variables": ["ao", "ls", "tc"],
                    "outlier_critical_value": 3.0
                }
            }
        }
        
        response = client.post(
            "/api/v1/x13/process",
            json=request
        )
        assert response.status_code == 200
        
        result = response.json()
        outliers = result["regarima_results"]["outliers"]
        assert len(outliers) > 0  # Should detect some outliers
    
    def test_result_not_found(self, client):
        """Test error handling for non-existent results."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(f"/api/v1/x13/results/{fake_id}")
        assert response.status_code == 404