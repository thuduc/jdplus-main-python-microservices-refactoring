"""Time series validation."""

from typing import List, Tuple
import numpy as np

from jdemetra_common.models import TsData


def validate_timeseries(ts: TsData) -> Tuple[bool, List[str], List[str]]:
    """
    Validate time series data.
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Check for empty series
    if len(ts.values) == 0:
        errors.append("Time series is empty")
        return False, errors, warnings
    
    # Check for NaN values
    nan_count = np.sum(np.isnan(ts.values))
    if nan_count > 0:
        errors.append(f"Time series contains {nan_count} NaN values")
    
    # Check for infinite values
    inf_count = np.sum(np.isinf(ts.values))
    if inf_count > 0:
        errors.append(f"Time series contains {inf_count} infinite values")
    
    # Check series length
    if len(ts.values) < 12:
        warnings.append("Time series has fewer than 12 observations")
    
    # Check for constant series
    if len(np.unique(ts.values)) == 1:
        warnings.append("Time series is constant")
    
    # Check for outliers (using IQR method)
    q1, q3 = np.percentile(ts.values[~np.isnan(ts.values)], [25, 75])
    iqr = q3 - q1
    if iqr > 0:
        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr
        outliers = np.sum((ts.values < lower_bound) | (ts.values > upper_bound))
        if outliers > 0:
            warnings.append(f"Time series contains {outliers} potential outliers")
    
    # Check for missing periods (gaps)
    # This is a simplified check - in reality would need more sophisticated gap detection
    if np.any(np.isnan(ts.values)):
        nan_positions = np.where(np.isnan(ts.values))[0]
        if len(nan_positions) > 1:
            gaps = np.diff(nan_positions)
            if np.any(gaps > 1):
                warnings.append("Time series contains gaps (non-consecutive missing values)")
    
    # Seasonal frequency validation
    if ts.frequency.value in ["M", "Q"] and len(ts.values) < ts.frequency.periods_per_year * 2:
        warnings.append(f"Time series has less than 2 complete {ts.frequency.value} cycles")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings