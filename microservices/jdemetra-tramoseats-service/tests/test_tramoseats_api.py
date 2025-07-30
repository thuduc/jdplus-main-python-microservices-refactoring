"""Tests for TRAMO/SEATS API."""

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

# Mock Celery task
class MockTask:
    def __init__(self):
        self.id = "test-job-123"
        self.state = "SUCCESS"
        self.result = {"result_id": "test-result-456"}

def mock_process_async(ts_data_dict, spec_dict):
    task = MockTask()
    return task

# Override dependencies
from src.main import app, get_redis
mock_redis = MockRedis()
app.dependency_overrides[get_redis] = lambda: mock_redis

# Mock Celery
from unittest.mock import patch


class TestTramoSeatsAPI:
    """Test TRAMO/SEATS API endpoints."""
    
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
    
    def test_process_sync(self, client, sample_timeseries):
        """Test synchronous processing."""
        response = client.post(
            "/api/v1/tramoseats/process",
            json=sample_timeseries
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "result_id" in result
        assert UUID(result["result_id"])
        assert result["status"] == "completed"
        
        # Check TRAMO results
        assert "tramo_results" in result
        tramo = result["tramo_results"]
        assert "model" in tramo
        assert "outliers" in tramo
        assert "residuals" in tramo
        
        # Check SEATS results
        assert "seats_results" in result
        seats = result["seats_results"]
        assert "trend" in seats
        assert "seasonal" in seats
        assert "irregular" in seats
        assert "seasonally_adjusted" in seats
        
        # Check components have correct length
        n = len(sample_timeseries["timeseries"]["values"])
        assert len(seats["seasonally_adjusted"]) == n
        assert len(seats["trend"]["values"]) == n
        assert len(seats["seasonal"]["values"]) == n
    
    @patch('src.api.tramoseats.process_tramoseats_async')
    def test_process_async(self, mock_task, client, sample_timeseries):
        """Test asynchronous processing."""
        mock_task.delay.return_value = MockTask()
        
        request = sample_timeseries.copy()
        request["async_processing"] = True
        
        response = client.post(
            "/api/v1/tramoseats/process",
            json=request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "job_id" in result
        assert result["status"] == "pending"
        assert "message" in result
    
    def test_process_with_specification(self, client, sample_timeseries):
        """Test processing with custom specification."""
        request = sample_timeseries.copy()
        request["specification"] = {
            "arima": {
                "p": 1,
                "d": 1,
                "q": 1,
                "bp": 0,
                "bd": 1,
                "bq": 1,
                "mean": True
            },
            "outlier": {
                "enabled": True,
                "types": ["AO", "LS"],
                "critical_value": 4.0
            },
            "calendar": {
                "trading_days": True,
                "easter": False,
                "leap_year": False
            },
            "transform": {
                "function": "log"
            },
            "decomposition": {
                "approximation": "legacy",
                "ma_unit_root_boundary": 0.95,
                "trend_boundary": 0.5,
                "seas_boundary": 0.8,
                "seas_boundary_at_pi": 0.8
            }
        }
        
        response = client.post(
            "/api/v1/tramoseats/process",
            json=request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["specification_used"]["transform"]["function"] == "log"
        assert result["specification_used"]["outlier"]["critical_value"] == 4.0
    
    def test_get_results(self, client, sample_timeseries):
        """Test retrieving results."""
        # First process
        process_response = client.post(
            "/api/v1/tramoseats/process",
            json=sample_timeseries
        )
        result_id = process_response.json()["result_id"]
        
        # Then retrieve
        response = client.get(f"/api/v1/tramoseats/results/{result_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert result["result_id"] == result_id
        assert "tramo_results" in result
        assert "seats_results" in result
    
    def test_create_specification(self, client):
        """Test specification creation."""
        specification = {
            "arima": {"p": 2, "d": 1, "q": 0},
            "outlier": {"enabled": False},
            "calendar": {"trading_days": False},
            "transform": {"function": "none"},
            "decomposition": {"approximation": "legacy"}
        }
        
        response = client.post(
            "/api/v1/tramoseats/specification",
            json=specification
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "specification_id" in result
        assert result["valid"] is True
        assert result["specification"]["arima"]["p"] == 2
    
    def test_diagnostics(self, client, sample_timeseries):
        """Test diagnostics."""
        # First process
        process_response = client.post(
            "/api/v1/tramoseats/process",
            json=sample_timeseries
        )
        result_id = process_response.json()["result_id"]
        
        # Run diagnostics
        diag_request = {
            "result_id": result_id,
            "tests": ["seasonality", "residuals", "spectral"]
        }
        
        response = client.post(
            "/api/v1/tramoseats/diagnostics",
            json=diag_request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["result_id"] == result_id
        assert "quality_measures" in result
        assert "m1" in result["quality_measures"]
        assert "q" in result["quality_measures"]
        
        # Check diagnostic tests
        assert "seasonality_tests" in result
        assert "residual_tests" in result
        assert "spectral_analysis" in result
    
    def test_result_not_found(self, client):
        """Test error handling for non-existent results."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(f"/api/v1/tramoseats/results/{fake_id}")
        assert response.status_code == 404
        
        diag_request = {
            "result_id": fake_id,
            "tests": ["seasonality"]
        }
        response = client.post("/api/v1/tramoseats/diagnostics", json=diag_request)
        assert response.status_code == 404
    
    @patch('src.api.tramoseats.celery_app.AsyncResult')
    def test_get_job_status(self, mock_async_result, client):
        """Test async job status checking."""
        # Mock different states
        mock_result = MockTask()
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/tramoseats/job/test-job-123")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"
        assert result["result_id"] == "test-result-456"