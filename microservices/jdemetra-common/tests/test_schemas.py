"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from jdemetra_common.schemas import (
    TsDataSchema, TsPeriodSchema,
    ArimaOrderSchema, ArimaModelSchema
)
from jdemetra_common.models import TsFrequency


class TestTsPeriodSchema:
    """Test TsPeriodSchema validation."""
    
    def test_valid_period(self):
        """Test valid period creation."""
        data = {"year": 2023, "period": 2, "frequency": "Q"}
        schema = TsPeriodSchema(**data)
        assert schema.year == 2023
        assert schema.period == 2
        assert schema.frequency == TsFrequency.QUARTERLY
    
    def test_period_validation(self):
        """Test period range validation."""
        # Valid quarterly period
        TsPeriodSchema(year=2023, period=4, frequency="Q")
        
        # Invalid quarterly period
        with pytest.raises(ValidationError) as exc_info:
            TsPeriodSchema(year=2023, period=5, frequency="Q")
        assert "exceeds maximum" in str(exc_info.value)
        
        # Valid monthly period
        TsPeriodSchema(year=2023, period=12, frequency="M")
        
        # Invalid monthly period
        with pytest.raises(ValidationError) as exc_info:
            TsPeriodSchema(year=2023, period=13, frequency="M")
        assert "exceeds maximum" in str(exc_info.value)


class TestTsDataSchema:
    """Test TsDataSchema validation."""
    
    def test_valid_data(self):
        """Test valid time series data."""
        data = {
            "values": [1.0, 2.0, 3.0],
            "start_period": {"year": 2023, "period": 1, "frequency": "M"},
            "frequency": "M",
            "metadata": {"source": "test"}
        }
        schema = TsDataSchema(**data)
        assert len(schema.values) == 3
        assert schema.metadata["source"] == "test"
    
    def test_empty_values_validation(self):
        """Test empty values validation."""
        data = {
            "values": [],
            "start_period": {"year": 2023, "period": 1, "frequency": "M"},
            "frequency": "M"
        }
        with pytest.raises(ValidationError) as exc_info:
            TsDataSchema(**data)
        assert "cannot be empty" in str(exc_info.value)
    
    def test_default_metadata(self):
        """Test default metadata."""
        data = {
            "values": [1.0],
            "start_period": {"year": 2023, "period": 1, "frequency": "Y"},
            "frequency": "Y"
        }
        schema = TsDataSchema(**data)
        assert schema.metadata == {}


class TestArimaOrderSchema:
    """Test ArimaOrderSchema validation."""
    
    def test_basic_order(self):
        """Test basic ARIMA order."""
        data = {"p": 1, "d": 1, "q": 1}
        schema = ArimaOrderSchema(**data)
        assert schema.p == 1
        assert schema.d == 1
        assert schema.q == 1
        assert schema.seasonal_period == 0
    
    def test_seasonal_order(self):
        """Test seasonal ARIMA order."""
        data = {
            "p": 1, "d": 1, "q": 1,
            "seasonal_p": 1, "seasonal_d": 1, "seasonal_q": 1,
            "seasonal_period": 12
        }
        schema = ArimaOrderSchema(**data)
        assert schema.seasonal_period == 12
    
    def test_negative_order_validation(self):
        """Test negative order validation."""
        with pytest.raises(ValidationError):
            ArimaOrderSchema(p=-1, d=0, q=0)
    
    def test_seasonal_period_validation(self):
        """Test seasonal period validation."""
        # Seasonal components without period should fail
        with pytest.raises(ValidationError) as exc_info:
            ArimaOrderSchema(p=1, d=0, q=0, seasonal_p=1)
        assert "Seasonal period must be > 0" in str(exc_info.value)


class TestArimaModelSchema:
    """Test ArimaModelSchema validation."""
    
    def test_valid_model(self):
        """Test valid ARIMA model."""
        data = {
            "order": {"p": 2, "d": 1, "q": 1},
            "ar_params": [0.5, 0.3],
            "ma_params": [0.7],
            "intercept": 0.1,
            "sigma2": 1.5,
            "aic": 100.0
        }
        schema = ArimaModelSchema(**data)
        assert len(schema.ar_params) == 2
        assert schema.aic == 100.0
    
    def test_minimal_model(self):
        """Test minimal model with defaults."""
        data = {
            "order": {"p": 0, "d": 1, "q": 0}
        }
        schema = ArimaModelSchema(**data)
        assert schema.intercept == 0.0
        assert schema.sigma2 == 1.0
        assert schema.ar_params is None
    
    def test_sigma2_validation(self):
        """Test sigma2 must be positive."""
        data = {
            "order": {"p": 0, "d": 0, "q": 0},
            "sigma2": -1.0
        }
        with pytest.raises(ValidationError):
            ArimaModelSchema(**data)