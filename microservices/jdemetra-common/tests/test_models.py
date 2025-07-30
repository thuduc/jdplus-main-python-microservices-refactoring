"""Tests for common models."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from jdemetra_common.models import (
    TsData, TsPeriod, TsFrequency,
    ArimaModel, ArimaOrder,
    ComponentType, DecompositionMode
)


class TestTsFrequency:
    """Test TsFrequency enum."""
    
    def test_periods_per_year(self):
        """Test periods per year calculation."""
        assert TsFrequency.YEARLY.periods_per_year == 1
        assert TsFrequency.QUARTERLY.periods_per_year == 4
        assert TsFrequency.MONTHLY.periods_per_year == 12
        assert TsFrequency.WEEKLY.periods_per_year == 52
        assert TsFrequency.DAILY.periods_per_year == 365
        assert TsFrequency.HOURLY.periods_per_year == 8760


class TestTsPeriod:
    """Test TsPeriod class."""
    
    def test_to_datetime_yearly(self):
        """Test datetime conversion for yearly frequency."""
        period = TsPeriod(2023, 1, TsFrequency.YEARLY)
        assert period.to_datetime() == datetime(2023, 1, 1)
    
    def test_to_datetime_quarterly(self):
        """Test datetime conversion for quarterly frequency."""
        period = TsPeriod(2023, 2, TsFrequency.QUARTERLY)
        assert period.to_datetime() == datetime(2023, 4, 1)
        
        period = TsPeriod(2023, 4, TsFrequency.QUARTERLY)
        assert period.to_datetime() == datetime(2023, 10, 1)
    
    def test_to_datetime_monthly(self):
        """Test datetime conversion for monthly frequency."""
        period = TsPeriod(2023, 6, TsFrequency.MONTHLY)
        assert period.to_datetime() == datetime(2023, 6, 1)
    
    def test_string_representation(self):
        """Test string representation."""
        assert str(TsPeriod(2023, 1, TsFrequency.YEARLY)) == "2023"
        assert str(TsPeriod(2023, 2, TsFrequency.QUARTERLY)) == "2023Q2"
        assert str(TsPeriod(2023, 6, TsFrequency.MONTHLY)) == "2023-06"


class TestTsData:
    """Test TsData class."""
    
    def test_initialization(self):
        """Test basic initialization."""
        values = [1.0, 2.0, 3.0, 4.0]
        start = TsPeriod(2023, 1, TsFrequency.QUARTERLY)
        ts = TsData(values, start, TsFrequency.QUARTERLY)
        
        assert ts.length == 4
        assert np.array_equal(ts.values, np.array(values))
        assert ts.frequency == TsFrequency.QUARTERLY
    
    def test_validation(self):
        """Test input validation."""
        start = TsPeriod(2023, 1, TsFrequency.MONTHLY)
        
        # Should convert list to numpy array
        ts = TsData([1, 2, 3], start, TsFrequency.MONTHLY)
        assert isinstance(ts.values, np.ndarray)
        
        # Should reject 2D array
        with pytest.raises(ValueError, match="1-dimensional"):
            TsData([[1, 2], [3, 4]], start, TsFrequency.MONTHLY)
    
    def test_end_period_calculation(self):
        """Test end period calculation."""
        # Yearly
        ts = TsData(
            [1, 2, 3],
            TsPeriod(2020, 1, TsFrequency.YEARLY),
            TsFrequency.YEARLY
        )
        assert ts.end_period.year == 2022
        
        # Quarterly
        ts = TsData(
            [1, 2, 3, 4, 5],
            TsPeriod(2020, 3, TsFrequency.QUARTERLY),
            TsFrequency.QUARTERLY
        )
        assert ts.end_period.year == 2021
        assert ts.end_period.period == 3
        
        # Monthly
        ts = TsData(
            [1] * 15,
            TsPeriod(2020, 11, TsFrequency.MONTHLY),
            TsFrequency.MONTHLY
        )
        assert ts.end_period.year == 2022
        assert ts.end_period.period == 1
    
    def test_pandas_conversion(self):
        """Test pandas conversion."""
        values = [1.0, 2.0, 3.0, 4.0]
        start = TsPeriod(2023, 1, TsFrequency.QUARTERLY)
        ts = TsData(values, start, TsFrequency.QUARTERLY)
        
        series = ts.to_pandas()
        assert isinstance(series, pd.Series)
        assert len(series) == 4
        assert series.index[0] == pd.Timestamp("2023-01-01")
        assert series.index[-1] == pd.Timestamp("2023-10-01")
    
    def test_from_pandas(self):
        """Test creation from pandas Series."""
        dates = pd.date_range("2023-01-01", periods=12, freq="MS")
        series = pd.Series(range(12), index=dates, name="test")
        
        ts = TsData.from_pandas(series, TsFrequency.MONTHLY)
        assert ts.length == 12
        assert ts.start_period.year == 2023
        assert ts.start_period.period == 1
        assert ts.metadata["name"] == "test"
    
    def test_serialization(self):
        """Test dict serialization."""
        values = [1.0, 2.0, 3.0]
        start = TsPeriod(2023, 2, TsFrequency.QUARTERLY)
        ts = TsData(values, start, TsFrequency.QUARTERLY, {"source": "test"})
        
        # To dict
        data = ts.to_dict()
        assert data["values"] == [1.0, 2.0, 3.0]
        assert data["start_period"]["year"] == 2023
        assert data["start_period"]["period"] == 2
        assert data["frequency"] == "Q"
        assert data["metadata"]["source"] == "test"
        
        # From dict
        ts2 = TsData.from_dict(data)
        assert np.array_equal(ts2.values, ts.values)
        assert ts2.start_period.year == ts.start_period.year
        assert ts2.frequency == ts.frequency


class TestArimaOrder:
    """Test ArimaOrder class."""
    
    def test_basic_order(self):
        """Test basic ARIMA order."""
        order = ArimaOrder(1, 1, 1)
        assert order.p == 1
        assert order.d == 1
        assert order.q == 1
        assert not order.is_seasonal
        assert order.to_tuple() == (1, 1, 1)
        assert str(order) == "ARIMA(1,1,1)"
    
    def test_seasonal_order(self):
        """Test seasonal ARIMA order."""
        order = ArimaOrder(1, 1, 1, 1, 1, 1, 12)
        assert order.is_seasonal
        assert order.to_tuple() == ((1, 1, 1), (1, 1, 1, 12))
        assert str(order) == "ARIMA(1,1,1)x(1,1,1)[12]"
    
    def test_validation(self):
        """Test order validation."""
        # Negative values should fail
        with pytest.raises(ValueError):
            ArimaOrder(-1, 0, 0)
        
        # Seasonal components without period should fail
        with pytest.raises(ValueError):
            ArimaOrder(1, 0, 0, seasonal_p=1)


class TestArimaModel:
    """Test ArimaModel class."""
    
    def test_basic_model(self):
        """Test basic ARIMA model."""
        order = ArimaOrder(2, 1, 1)
        model = ArimaModel(
            order=order,
            ar_params=[0.5, 0.3],
            ma_params=[0.7],
            intercept=0.1,
            sigma2=1.5
        )
        
        assert model.n_parameters == 4  # 2 AR + 1 MA + 1 intercept
        assert len(model.ar_params) == 2
        assert len(model.ma_params) == 1
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        order = ArimaOrder(2, 0, 1)
        
        # Wrong number of AR parameters
        with pytest.raises(ValueError, match="Expected 2 AR parameters"):
            ArimaModel(order=order, ar_params=[0.5])
        
        # Wrong number of MA parameters
        with pytest.raises(ValueError, match="Expected 1 MA parameters"):
            ArimaModel(order=order, ma_params=[0.5, 0.3])
    
    def test_serialization(self):
        """Test model serialization."""
        order = ArimaOrder(1, 0, 1)
        model = ArimaModel(
            order=order,
            ar_params=[0.7],
            ma_params=[0.3],
            intercept=0.5,
            sigma2=2.0,
            aic=100.0
        )
        
        # To dict
        data = model.to_dict()
        assert data["ar_params"] == [0.7]
        assert data["ma_params"] == [0.3]
        assert data["aic"] == 100.0
        
        # From dict
        model2 = ArimaModel.from_dict(data)
        assert np.array_equal(model2.ar_params, model.ar_params)
        assert model2.aic == model.aic


class TestEnums:
    """Test enumeration classes."""
    
    def test_component_type(self):
        """Test ComponentType enum."""
        assert ComponentType.TREND.value == "trend"
        assert ComponentType.SEASONAL.value == "seasonal"
        assert len(ComponentType) == 7
    
    def test_decomposition_mode(self):
        """Test DecompositionMode enum."""
        assert DecompositionMode.ADDITIVE.value == "additive"
        assert DecompositionMode.MULTIPLICATIVE.value == "multiplicative"
        assert len(DecompositionMode) == 4