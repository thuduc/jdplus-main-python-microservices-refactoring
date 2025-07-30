"""Tests for time series validation."""

import pytest
import numpy as np

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from src.core.validation import validate_timeseries


class TestValidation:
    """Test validation functions."""
    
    def create_test_series(self, values, frequency="M"):
        """Create test time series."""
        return TsData(
            values=np.array(values),
            start_period=TsPeriod(2023, 1, TsFrequency(frequency)),
            frequency=TsFrequency(frequency)
        )
    
    def test_validate_empty_series(self):
        """Test validation of empty series."""
        ts = self.create_test_series([])
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert not is_valid
        assert len(errors) == 1
        assert "empty" in errors[0]
    
    def test_validate_nan_values(self):
        """Test validation with NaN values."""
        ts = self.create_test_series([1.0, 2.0, np.nan, 4.0, np.nan])
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert not is_valid
        assert any("NaN" in error for error in errors)
        assert "2 NaN values" in errors[0]
    
    def test_validate_infinite_values(self):
        """Test validation with infinite values."""
        ts = self.create_test_series([1.0, 2.0, np.inf, 4.0, -np.inf])
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert not is_valid
        assert any("infinite" in error for error in errors)
        assert "2 infinite values" in errors[0]
    
    def test_validate_short_series(self):
        """Test validation of short series."""
        ts = self.create_test_series([1.0, 2.0, 3.0])
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert is_valid
        assert len(warnings) == 1
        assert "fewer than 12 observations" in warnings[0]
    
    def test_validate_constant_series(self):
        """Test validation of constant series."""
        ts = self.create_test_series([5.0] * 20)
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert is_valid
        assert any("constant" in warning for warning in warnings)
    
    def test_validate_outliers(self):
        """Test validation with outliers."""
        # Create series with outliers
        values = list(np.random.normal(100, 10, 50))
        values[10] = 300  # Outlier
        values[20] = -50  # Outlier
        
        ts = self.create_test_series(values)
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert is_valid
        assert any("outliers" in warning for warning in warnings)
    
    def test_validate_gaps(self):
        """Test validation with gaps (non-consecutive NaN)."""
        values = [1.0, 2.0, np.nan, 4.0, 5.0, np.nan, np.nan, 8.0]
        ts = self.create_test_series(values)
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert not is_valid  # Has NaN values
        # Gap detection would trigger if there are non-consecutive NaNs
    
    def test_validate_seasonal_series(self):
        """Test validation of seasonal series."""
        # Monthly series with less than 2 years
        ts = self.create_test_series([1.0] * 18, "M")
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert is_valid
        assert any("less than 2 complete" in warning for warning in warnings)
        
        # Quarterly series with less than 2 years
        ts_q = self.create_test_series([1.0] * 6, "Q")
        is_valid_q, errors_q, warnings_q = validate_timeseries(ts_q)
        
        assert is_valid_q
        assert any("less than 2 complete" in warning for warning in warnings_q)
    
    def test_validate_valid_series(self):
        """Test validation of a completely valid series."""
        # Create a good series
        values = 100 + 10 * np.sin(np.linspace(0, 4*np.pi, 50)) + np.random.normal(0, 2, 50)
        ts = self.create_test_series(values, "M")
        
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert is_valid
        assert len(errors) == 0
        # Might have some warnings depending on random values
    
    def test_validate_mixed_issues(self):
        """Test validation with multiple issues."""
        # Series with NaN, short length, and constant remaining values
        values = [5.0, np.nan, 5.0, 5.0, 5.0]
        ts = self.create_test_series(values)
        
        is_valid, errors, warnings = validate_timeseries(ts)
        
        assert not is_valid  # Has NaN
        assert len(errors) >= 1
        assert len(warnings) >= 2  # Short and constant