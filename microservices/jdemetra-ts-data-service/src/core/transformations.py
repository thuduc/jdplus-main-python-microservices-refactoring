"""Time series transformations."""

import numpy as np
from typing import Dict, Any

from jdemetra_common.models import TsData


def apply_transformation(ts: TsData, operation: str, parameters: Dict[str, Any]) -> TsData:
    """Apply transformation to time series."""
    
    if operation == "log":
        return log_transform(ts)
    elif operation == "sqrt":
        return sqrt_transform(ts)
    elif operation == "diff":
        lag = parameters.get("lag", 1)
        return difference(ts, lag)
    elif operation == "seasonal_diff":
        period = parameters.get("period", ts.frequency.periods_per_year)
        return seasonal_difference(ts, period)
    elif operation == "standardize":
        return standardize(ts)
    elif operation == "detrend":
        return detrend(ts)
    else:
        raise ValueError(f"Unknown transformation: {operation}")


def log_transform(ts: TsData) -> TsData:
    """Apply log transformation."""
    if np.any(ts.values <= 0):
        raise ValueError("Cannot apply log transformation to non-positive values")
    
    return TsData(
        values=np.log(ts.values),
        start_period=ts.start_period,
        frequency=ts.frequency,
        metadata={**ts.metadata, "transformation": "log"}
    )


def sqrt_transform(ts: TsData) -> TsData:
    """Apply square root transformation."""
    if np.any(ts.values < 0):
        raise ValueError("Cannot apply sqrt transformation to negative values")
    
    return TsData(
        values=np.sqrt(ts.values),
        start_period=ts.start_period,
        frequency=ts.frequency,
        metadata={**ts.metadata, "transformation": "sqrt"}
    )


def difference(ts: TsData, lag: int = 1) -> TsData:
    """Apply differencing."""
    if lag >= len(ts.values):
        raise ValueError(f"Lag {lag} exceeds series length {len(ts.values)}")
    
    diff_values = np.diff(ts.values, n=lag)
    
    # Adjust start period
    new_start = ts.start_period
    for _ in range(lag):
        if ts.frequency.value == "M":
            if new_start.period == 12:
                new_start.year += 1
                new_start.period = 1
            else:
                new_start.period += 1
        elif ts.frequency.value == "Q":
            if new_start.period == 4:
                new_start.year += 1
                new_start.period = 1
            else:
                new_start.period += 1
        elif ts.frequency.value == "Y":
            new_start.year += 1
    
    return TsData(
        values=diff_values,
        start_period=new_start,
        frequency=ts.frequency,
        metadata={**ts.metadata, "transformation": f"diff({lag})"}
    )


def seasonal_difference(ts: TsData, period: int) -> TsData:
    """Apply seasonal differencing."""
    if period >= len(ts.values):
        raise ValueError(f"Period {period} exceeds series length {len(ts.values)}")
    
    sdiff_values = ts.values[period:] - ts.values[:-period]
    
    # Adjust start period by the seasonal period
    new_start = ts.start_period
    if ts.frequency.value == "M":
        total_months = new_start.year * 12 + new_start.period - 1 + period
        new_start.year = total_months // 12
        new_start.period = (total_months % 12) + 1
    elif ts.frequency.value == "Q":
        total_quarters = new_start.year * 4 + new_start.period - 1 + period
        new_start.year = total_quarters // 4
        new_start.period = (total_quarters % 4) + 1
    elif ts.frequency.value == "Y":
        new_start.year += period
    
    return TsData(
        values=sdiff_values,
        start_period=new_start,
        frequency=ts.frequency,
        metadata={**ts.metadata, "transformation": f"seasonal_diff({period})"}
    )


def standardize(ts: TsData) -> TsData:
    """Standardize to zero mean and unit variance."""
    mean = np.mean(ts.values)
    std = np.std(ts.values, ddof=1)
    
    if std == 0:
        raise ValueError("Cannot standardize series with zero variance")
    
    return TsData(
        values=(ts.values - mean) / std,
        start_period=ts.start_period,
        frequency=ts.frequency,
        metadata={
            **ts.metadata,
            "transformation": "standardize",
            "original_mean": float(mean),
            "original_std": float(std)
        }
    )


def detrend(ts: TsData) -> TsData:
    """Remove linear trend."""
    n = len(ts.values)
    x = np.arange(n)
    
    # Fit linear trend
    coeffs = np.polyfit(x, ts.values, 1)
    trend = np.polyval(coeffs, x)
    
    return TsData(
        values=ts.values - trend,
        start_period=ts.start_period,
        frequency=ts.frequency,
        metadata={
            **ts.metadata,
            "transformation": "detrend",
            "trend_slope": float(coeffs[0]),
            "trend_intercept": float(coeffs[1])
        }
    )