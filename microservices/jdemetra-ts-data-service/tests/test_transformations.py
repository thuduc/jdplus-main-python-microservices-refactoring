"""Tests for time series transformations."""

import pytest
import numpy as np

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from src.core.transformations import (
    log_transform, sqrt_transform, difference, 
    seasonal_difference, standardize, detrend,
    apply_transformation
)


class TestTransformations:
    """Test transformation functions."""
    
    def create_test_series(self, values, frequency="M"):
        """Create test time series."""
        return TsData(
            values=np.array(values),
            start_period=TsPeriod(2023, 1, TsFrequency(frequency)),
            frequency=TsFrequency(frequency)
        )
    
    def test_log_transform(self):
        """Test log transformation."""
        ts = self.create_test_series([1.0, 2.0, 3.0, 4.0])
        result = log_transform(ts)
        
        assert len(result.values) == 4
        assert np.allclose(result.values, np.log([1.0, 2.0, 3.0, 4.0]))
        assert result.metadata["transformation"] == "log"
        
        # Test with non-positive values
        ts_invalid = self.create_test_series([1.0, 0.0, -1.0])
        with pytest.raises(ValueError, match="non-positive"):
            log_transform(ts_invalid)
    
    def test_sqrt_transform(self):
        """Test square root transformation."""
        ts = self.create_test_series([1.0, 4.0, 9.0, 16.0])
        result = sqrt_transform(ts)
        
        assert len(result.values) == 4
        assert np.allclose(result.values, [1.0, 2.0, 3.0, 4.0])
        assert result.metadata["transformation"] == "sqrt"
        
        # Test with negative values
        ts_invalid = self.create_test_series([1.0, -4.0])
        with pytest.raises(ValueError, match="negative"):
            sqrt_transform(ts_invalid)
    
    def test_difference(self):
        """Test differencing."""
        ts = self.create_test_series([1.0, 3.0, 6.0, 10.0])
        result = difference(ts, lag=1)
        
        assert len(result.values) == 3
        assert np.allclose(result.values, [2.0, 3.0, 4.0])
        assert result.start_period.period == 2  # Started at 1, now 2
        assert result.metadata["transformation"] == "diff(1)"
        
        # Test lag=2
        result2 = difference(ts, lag=2)
        assert len(result2.values) == 2
        assert np.allclose(result2.values, [5.0, 7.0])
        
        # Test invalid lag
        with pytest.raises(ValueError, match="exceeds series length"):
            difference(ts, lag=10)
    
    def test_seasonal_difference(self):
        """Test seasonal differencing."""
        # Monthly data with seasonal pattern
        values = [100 + 10*i + 5*np.sin(i*np.pi/6) for i in range(24)]
        ts = self.create_test_series(values, "M")
        
        result = seasonal_difference(ts, period=12)
        assert len(result.values) == 12
        assert result.start_period.year == 2024  # Started 2023, +12 months
        assert result.start_period.period == 1
        
        # Test with quarterly data
        ts_q = self.create_test_series([1, 2, 3, 4, 5, 6, 7, 8], "Q")
        result_q = seasonal_difference(ts_q, period=4)
        assert len(result_q.values) == 4
        assert np.allclose(result_q.values, [4, 4, 4, 4])
    
    def test_standardize(self):
        """Test standardization."""
        ts = self.create_test_series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = standardize(ts)
        
        # Check mean is approximately 0 and std is approximately 1
        assert abs(np.mean(result.values)) < 1e-10
        assert abs(np.std(result.values, ddof=1) - 1.0) < 1e-10
        
        # Check metadata
        assert "original_mean" in result.metadata
        assert "original_std" in result.metadata
        assert result.metadata["transformation"] == "standardize"
        
        # Test constant series
        ts_const = self.create_test_series([5.0, 5.0, 5.0])
        with pytest.raises(ValueError, match="zero variance"):
            standardize(ts_const)
    
    def test_detrend(self):
        """Test detrending."""
        # Create series with trend
        values = [10 + 2*i + np.random.normal(0, 0.1) for i in range(20)]
        ts = self.create_test_series(values)
        
        result = detrend(ts)
        
        # Detrended series should have no linear trend
        x = np.arange(len(result.values))
        coeffs = np.polyfit(x, result.values, 1)
        assert abs(coeffs[0]) < 0.1  # Slope should be near zero
        
        # Check metadata
        assert "trend_slope" in result.metadata
        assert "trend_intercept" in result.metadata
        assert abs(result.metadata["trend_slope"] - 2.0) < 0.5  # Should be close to 2
    
    def test_apply_transformation(self):
        """Test apply_transformation dispatcher."""
        ts = self.create_test_series([1.0, 4.0, 9.0, 16.0])
        
        # Test various operations
        result_log = apply_transformation(ts, "log", {})
        assert result_log.metadata["transformation"] == "log"
        
        result_diff = apply_transformation(ts, "diff", {"lag": 1})
        assert len(result_diff.values) == 3
        
        result_sdiff = apply_transformation(ts, "seasonal_diff", {"period": 2})
        assert len(result_sdiff.values) == 2
        
        # Test unknown operation
        with pytest.raises(ValueError, match="Unknown transformation"):
            apply_transformation(ts, "unknown_op", {})
    
    def test_transformation_chain(self):
        """Test applying multiple transformations."""
        # Create series with trend and seasonality
        t = np.arange(36)
        values = 100 + 2*t + 10*np.sin(2*np.pi*t/12) + np.random.normal(0, 1, 36)
        ts = self.create_test_series(values, "M")
        
        # Apply log then difference
        ts_log = log_transform(ts)
        ts_diff = difference(ts_log, lag=1)
        
        assert len(ts_diff.values) == 35
        assert ts_diff.start_period.period == 2
        
        # The differenced log series should be more stationary
        assert np.std(ts_diff.values) < np.std(np.diff(values))