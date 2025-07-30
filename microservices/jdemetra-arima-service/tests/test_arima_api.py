"""Tests for ARIMA API."""

import pytest
import numpy as np
from uuid import UUID
from fastapi.testclient import TestClient

# Mock Redis for testing
class MockRedis:
    def __init__(self):
        self.data = {}
    
    async def setex(self, key, ttl, value):
        self.data[key] = value
    
    async def get(self, key):
        return self.data.get(key)
    
    async def delete(self, key):
        if key in self.data:
            del self.data[key]
            return 1
        return 0

# Override dependencies
from src.main import app, get_redis
mock_redis = MockRedis()
app.dependency_overrides[get_redis] = lambda: mock_redis


class TestArimaAPI:
    """Test ARIMA API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_timeseries(self):
        """Generate sample time series data."""
        np.random.seed(42)
        # AR(1) process
        n = 100
        ar_coef = 0.7
        data = [0]
        for i in range(1, n):
            data.append(ar_coef * data[i-1] + np.random.normal(0, 1))
        
        return {
            "timeseries": {
                "values": data,
                "start_period": {"year": 2020, "period": 1, "frequency": "M"},
                "frequency": "M",
                "metadata": {"name": "AR(1) test series"}
            }
        }
    
    def test_estimate_auto(self, client, sample_timeseries):
        """Test automatic ARIMA estimation."""
        response = client.post(
            "/api/v1/arima/estimate",
            json=sample_timeseries
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "model_id" in result
        assert UUID(result["model_id"])  # Valid UUID
        assert "model" in result
        assert "fit_time" in result
        assert result["fit_time"] > 0
        
        # Check model structure
        model = result["model"]
        assert "order" in model
        assert model["order"]["p"] >= 0
        assert model["order"]["d"] >= 0
        assert model["order"]["q"] >= 0
    
    def test_estimate_with_order(self, client, sample_timeseries):
        """Test ARIMA estimation with specified order."""
        request = sample_timeseries.copy()
        request["order"] = {"p": 1, "d": 0, "q": 1}
        
        response = client.post(
            "/api/v1/arima/estimate",
            json=request
        )
        assert response.status_code == 200
        
        result = response.json()
        model = result["model"]
        assert model["order"]["p"] == 1
        assert model["order"]["d"] == 0
        assert model["order"]["q"] == 1
    
    def test_forecast(self, client, sample_timeseries):
        """Test forecasting."""
        # First estimate a model
        est_response = client.post(
            "/api/v1/arima/estimate",
            json=sample_timeseries
        )
        model_id = est_response.json()["model_id"]
        
        # Then forecast
        forecast_request = {
            "model_id": model_id,
            "horizon": 12,
            "confidence_level": 0.95
        }
        
        response = client.post(
            "/api/v1/arima/forecast",
            json=forecast_request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["model_id"] == model_id
        assert len(result["forecasts"]) == 12
        assert result["confidence_level"] == 0.95
        
        # Check forecast structure
        forecast = result["forecasts"][0]
        assert "period" in forecast
        assert "forecast" in forecast
        assert "lower_bound" in forecast
        assert "upper_bound" in forecast
        assert forecast["lower_bound"] < forecast["forecast"] < forecast["upper_bound"]
    
    def test_identify(self, client, sample_timeseries):
        """Test automatic model identification."""
        request = {
            "timeseries": sample_timeseries["timeseries"],
            "seasonal": False,  # Non-seasonal for speed
            "stepwise": True,
            "max_p": 3,
            "max_q": 3,
            "max_d": 1,
            "information_criterion": "aic"
        }
        
        response = client.post(
            "/api/v1/arima/identify",
            json=request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "best_model" in result
        assert "search_summary" in result
        assert "candidates_evaluated" in result
        assert result["candidates_evaluated"] > 0
        assert result["identification_time"] > 0
    
    def test_get_model(self, client, sample_timeseries):
        """Test retrieving saved model."""
        # First estimate
        est_response = client.post(
            "/api/v1/arima/estimate",
            json=sample_timeseries
        )
        model_id = est_response.json()["model_id"]
        
        # Then retrieve
        response = client.get(f"/api/v1/arima/model/{model_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert result["model_id"] == model_id
        assert "model" in result
        assert "timeseries_info" in result
    
    def test_diagnose(self, client, sample_timeseries):
        """Test model diagnostics."""
        # First estimate
        est_response = client.post(
            "/api/v1/arima/estimate",
            json=sample_timeseries
        )
        model_id = est_response.json()["model_id"]
        
        # Then diagnose
        diagnose_request = {
            "model_id": model_id,
            "tests": ["ljung_box", "jarque_bera"]
        }
        
        response = client.post(
            "/api/v1/arima/diagnose",
            json=diagnose_request
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["model_id"] == model_id
        assert "residual_stats" in result
        assert "diagnostic_tests" in result
        assert len(result["diagnostic_tests"]) == 2
        
        # Check test structure
        test = result["diagnostic_tests"][0]
        assert "test_name" in test
        assert "statistic" in test
        assert "p_value" in test
        assert "conclusion" in test
    
    def test_model_not_found(self, client):
        """Test error handling for non-existent model."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(f"/api/v1/arima/model/{fake_id}")
        assert response.status_code == 404
        
        forecast_request = {
            "model_id": fake_id,
            "horizon": 12,
            "confidence_level": 0.95
        }
        response = client.post("/api/v1/arima/forecast", json=forecast_request)
        assert response.status_code == 404
    
    def test_invalid_order(self, client, sample_timeseries):
        """Test validation of ARIMA order."""
        request = sample_timeseries.copy()
        request["order"] = {"p": 10, "d": 0, "q": 0}  # Exceeds max
        
        response = client.post(
            "/api/v1/arima/estimate",
            json=request
        )
        assert response.status_code == 422  # Validation error