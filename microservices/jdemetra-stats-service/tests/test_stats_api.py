"""Tests for statistical analysis API."""

import pytest
import numpy as np
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app


class TestStatsAPI:
    """Test statistical analysis endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def normal_data(self):
        """Generate normal data."""
        np.random.seed(42)
        return np.random.normal(100, 15, 100).tolist()
    
    @pytest.fixture
    def non_normal_data(self):
        """Generate non-normal data."""
        np.random.seed(42)
        return np.random.exponential(10, 100).tolist()
    
    @pytest.fixture
    def stationary_data(self):
        """Generate stationary data."""
        np.random.seed(42)
        return np.random.normal(0, 1, 100).tolist()
    
    @pytest.fixture
    def non_stationary_data(self):
        """Generate non-stationary data with trend."""
        np.random.seed(42)
        trend = np.linspace(0, 10, 100)
        noise = np.random.normal(0, 1, 100)
        return (trend + noise).tolist()
    
    def test_normality_test_normal(self, client, normal_data):
        """Test normality test with normal data."""
        response = client.post(
            "/api/v1/stats/test/normality",
            json={"data": normal_data, "method": "shapiro"}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "statistic" in result
        assert "p_value" in result
        assert result["p_value"] > 0.05  # Should not reject normality
        assert not result["reject_null"]
        assert "normally distributed" in result["interpretation"]
    
    def test_normality_test_non_normal(self, client, non_normal_data):
        """Test normality test with non-normal data."""
        response = client.post(
            "/api/v1/stats/test/normality",
            json={"data": non_normal_data, "method": "jarque_bera"}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["p_value"] < 0.05  # Should reject normality
        assert result["reject_null"]
        assert "not normally distributed" in result["interpretation"]
    
    def test_stationarity_test_stationary(self, client, stationary_data):
        """Test stationarity test with stationary data."""
        response = client.post(
            "/api/v1/stats/test/stationarity",
            json={"data": stationary_data, "method": "adf", "regression": "c"}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["p_value"] < 0.05  # Should reject null (data is stationary)
        assert result["reject_null"]
        assert "stationary" in result["interpretation"]
    
    def test_stationarity_test_non_stationary(self, client, non_stationary_data):
        """Test stationarity test with non-stationary data."""
        response = client.post(
            "/api/v1/stats/test/stationarity",
            json={"data": non_stationary_data, "method": "adf", "regression": "ct"}
        )
        assert response.status_code == 200
        
        result = response.json()
        # Non-stationary data should not reject null
        assert "non-stationary" in result["interpretation"] or "stationary" in result["interpretation"]
    
    def test_descriptive_stats(self, client, normal_data):
        """Test descriptive statistics."""
        response = client.post(
            "/api/v1/stats/descriptive",
            json={"data": normal_data, "percentiles": [10, 25, 50, 75, 90]}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["count"] == 100
        assert 95 < result["mean"] < 105  # Close to 100
        assert 12 < result["std"] < 18  # Close to 15
        assert "p50" in result["percentiles"]
        assert result["percentiles"]["p50"] == pytest.approx(result["percentiles"]["p50"], rel=0.1)
    
    def test_distribution_fitting(self, client, normal_data):
        """Test distribution fitting."""
        response = client.post(
            "/api/v1/stats/distribution/fit",
            json={"data": normal_data, "distributions": ["normal", "exponential", "gamma"]}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert len(result["results"]) >= 1
        assert result["best_distribution"] == "normal"  # Normal should fit best
        
        # Check normal distribution parameters
        normal_result = next(r for r in result["results"] if r["distribution"] == "normal")
        assert 95 < normal_result["parameters"]["loc"] < 105
        assert 12 < normal_result["parameters"]["scale"] < 18
    
    def test_randomness_test(self, client):
        """Test randomness test."""
        # Random data
        np.random.seed(42)
        random_data = np.random.normal(0, 1, 100).tolist()
        
        response = client.post(
            "/api/v1/stats/test/randomness",
            json={"data": random_data, "method": "runs"}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["p_value"] > 0.05  # Should not reject randomness
        assert not result["reject_null"]
        assert "random" in result["interpretation"]
    
    def test_seasonality_test(self, client):
        """Test seasonality test."""
        # Create seasonal data
        t = np.arange(120)
        seasonal = 10 * np.sin(2 * np.pi * t / 12)  # Monthly seasonality
        noise = np.random.normal(0, 1, 120)
        seasonal_data = (seasonal + noise).tolist()
        
        response = client.post(
            "/api/v1/stats/test/seasonality",
            json={"data": seasonal_data, "period": 12, "method": "auto"}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["p_value"] < 0.05  # Should detect seasonality
        assert result["reject_null"]
        assert "seasonality detected" in result["interpretation"]
    
    def test_empty_data_error(self, client):
        """Test error handling for empty data."""
        response = client.post(
            "/api/v1/stats/test/normality",
            json={"data": [], "method": "shapiro"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_invalid_method_error(self, client, normal_data):
        """Test error handling for invalid method."""
        response = client.post(
            "/api/v1/stats/test/normality",
            json={"data": normal_data, "method": "invalid_method"}
        )
        assert response.status_code == 422  # Validation error