"""Descriptive statistics computation."""

import numpy as np
from scipy import stats
from typing import List, Dict


def compute_descriptive_stats(data: np.ndarray, percentiles: List[float] = None) -> Dict[str, float]:
    """
    Compute comprehensive descriptive statistics.
    
    Args:
        data: Input data array
        percentiles: List of percentiles to compute (default: [25, 50, 75])
        
    Returns:
        Dictionary of statistics
    """
    if percentiles is None:
        percentiles = [25, 50, 75]
    
    # Basic statistics
    n = len(data)
    mean = np.mean(data)
    std = np.std(data, ddof=1)  # Sample standard deviation
    variance = np.var(data, ddof=1)
    min_val = np.min(data)
    max_val = np.max(data)
    
    # Percentiles
    percentile_values = np.percentile(data, percentiles)
    percentile_dict = {f"p{int(p)}": float(val) for p, val in zip(percentiles, percentile_values)}
    
    # Higher moments
    skewness = stats.skew(data)
    kurtosis = stats.kurtosis(data, fisher=True)  # Excess kurtosis
    
    # Coefficient of variation
    cv = std / mean if mean != 0 else None
    
    return {
        "count": n,
        "mean": float(mean),
        "std": float(std),
        "variance": float(variance),
        "min": float(min_val),
        "max": float(max_val),
        "percentiles": percentile_dict,
        "skewness": float(skewness),
        "kurtosis": float(kurtosis),
        "coefficient_of_variation": float(cv) if cv is not None else None
    }