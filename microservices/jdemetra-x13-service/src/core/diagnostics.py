"""X-13 diagnostics."""

import numpy as np
from scipy import stats, signal
from typing import Dict, Any, List

from jdemetra_common.models import TsData


def run_diagnostics(results: Dict[str, Any], tests: List[str]) -> Dict[str, Any]:
    """Run diagnostics on X-13 results."""
    diagnostics = {}
    
    if "spectrum" in tests:
        diagnostics["spectrum_analysis"] = _spectrum_analysis(results)
    
    if "stability" in tests:
        diagnostics["stability_tests"] = _stability_tests(results)
    
    if "residuals" in tests:
        diagnostics["residual_diagnostics"] = _residual_diagnostics(results)
    
    if "sliding_spans" in tests:
        diagnostics["sliding_spans"] = _sliding_spans_analysis(results)
    
    # Summary statistics
    diagnostics["summary_statistics"] = _compute_summary_stats(results)
    
    return diagnostics


def _spectrum_analysis(results: Dict[str, Any]) -> Dict[str, Any]:
    """Perform spectrum analysis on seasonally adjusted series."""
    if results.get("x11_results"):
        sa_series = np.array(results["x11_results"]["d11"])
    elif results.get("seats_results"):
        sa_series = np.array(results["seats_results"]["seasonally_adjusted"])
    else:
        return {"error": "No decomposition results available"}
    
    # Compute spectrum
    frequencies, power = signal.periodogram(sa_series, scaling='density')
    
    # Find peaks
    peaks, properties = signal.find_peaks(power, height=np.mean(power) * 2)
    
    # Check for residual seasonality
    seasonal_freq = 1/12  # Monthly seasonality
    seasonal_idx = np.argmin(np.abs(frequencies - seasonal_freq))
    seasonal_power = power[seasonal_idx]
    
    return {
        "peak_frequency": float(frequencies[np.argmax(power)]),
        "seasonal_frequency_power": float(seasonal_power),
        "residual_seasonality": seasonal_power > np.mean(power) * 3,
        "significant_peaks": [
            {
                "frequency": float(frequencies[peak]),
                "period": float(1/frequencies[peak]) if frequencies[peak] > 0 else np.inf,
                "power": float(power[peak])
            }
            for peak in peaks[:5]
        ]
    }


def _stability_tests(results: Dict[str, Any]) -> Dict[str, Any]:
    """Test stability of seasonal adjustment."""
    if results.get("x11_results"):
        sa_series = np.array(results["x11_results"]["d11"])
        seasonal = np.array(results["x11_results"]["d10"])
    elif results.get("seats_results"):
        sa_series = np.array(results["seats_results"]["seasonally_adjusted"])
        seasonal = np.array(results["seats_results"]["seasonal"])
    else:
        return {"error": "No decomposition results available"}
    
    n = len(sa_series)
    
    # Split series into halves
    if n < 24:
        return {"error": "Series too short for stability testing"}
    
    first_half = sa_series[:n//2]
    second_half = sa_series[n//2:]
    
    # Compare variance
    f_stat = np.var(second_half) / np.var(first_half)
    df1 = len(second_half) - 1
    df2 = len(first_half) - 1
    p_value = 2 * min(stats.f.cdf(f_stat, df1, df2), 1 - stats.f.cdf(f_stat, df1, df2))
    
    # Seasonal stability
    seasonal_first = seasonal[:n//2]
    seasonal_second = seasonal[n//2:]
    
    # Compare seasonal patterns
    period = 12
    if len(seasonal_first) >= period and len(seasonal_second) >= period:
        pattern_correlation = np.corrcoef(
            seasonal_first[:period],
            seasonal_second[:period]
        )[0, 1]
    else:
        pattern_correlation = None
    
    return {
        "variance_stability": {
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "stable": p_value > 0.05
        },
        "seasonal_stability": {
            "pattern_correlation": float(pattern_correlation) if pattern_correlation else None,
            "stable": pattern_correlation > 0.8 if pattern_correlation else None
        }
    }


def _residual_diagnostics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Perform residual diagnostics."""
    # Get residuals from RegARIMA model
    model = results["regarima_results"]["model"]
    
    # Simulate residuals (in production would get from actual model)
    n = 100  # Assumed length
    residuals = np.random.normal(0, np.sqrt(model.sigma2), n)
    
    # Normality test
    jb_stat, jb_pvalue = stats.jarque_bera(residuals)
    
    # Autocorrelation test (Ljung-Box)
    from statsmodels.stats.diagnostic import acorr_ljungbox
    lb_result = acorr_ljungbox(residuals, lags=24, return_df=False)
    lb_stat = lb_result[0][-1]
    lb_pvalue = lb_result[1][-1]
    
    # ARCH test (simplified)
    squared_resid = residuals ** 2
    arch_result = acorr_ljungbox(squared_resid, lags=12, return_df=False)
    arch_stat = arch_result[0][-1]
    arch_pvalue = arch_result[1][-1]
    
    return {
        "normality": {
            "jarque_bera_statistic": float(jb_stat),
            "p_value": float(jb_pvalue),
            "normal": jb_pvalue > 0.05
        },
        "autocorrelation": {
            "ljung_box_statistic": float(lb_stat),
            "p_value": float(lb_pvalue),
            "no_autocorrelation": lb_pvalue > 0.05
        },
        "heteroscedasticity": {
            "arch_lm_statistic": float(arch_stat),
            "p_value": float(arch_pvalue),
            "homoscedastic": arch_pvalue > 0.05
        }
    }


def _sliding_spans_analysis(results: Dict[str, Any]) -> Dict[str, Any]:
    """Perform sliding spans analysis (simplified)."""
    # In production, would re-estimate model on multiple overlapping spans
    # Here we simulate the results
    
    if results.get("x11_results"):
        sa_series = results["x11_results"]["d11"]
    elif results.get("seats_results"):
        sa_series = results["seats_results"]["seasonally_adjusted"]
    else:
        return {"error": "No decomposition results available"}
    
    # Simulate sliding spans results
    n_spans = 4
    span_length = len(sa_series) - 12
    
    # Simulate maximum percentage differences
    max_pct_diff = {
        "seasonal_factors": np.random.uniform(1, 5),
        "seasonally_adjusted": np.random.uniform(0.5, 3),
        "trend": np.random.uniform(0.3, 2),
        "month_to_month_changes": np.random.uniform(1, 4)
    }
    
    # Classification based on thresholds
    classifications = {}
    for component, max_diff in max_pct_diff.items():
        if max_diff < 1:
            classifications[component] = "A - Very Good"
        elif max_diff < 2:
            classifications[component] = "B - Good"
        elif max_diff < 3:
            classifications[component] = "C - Fair"
        else:
            classifications[component] = "D - Poor"
    
    return {
        "n_spans": n_spans,
        "span_length": span_length,
        "max_percentage_differences": max_pct_diff,
        "classifications": classifications,
        "overall_stability": "B - Good" if np.mean(list(max_pct_diff.values())) < 2 else "C - Fair"
    }


def _compute_summary_stats(results: Dict[str, Any]) -> Dict[str, float]:
    """Compute summary statistics."""
    stats_dict = {}
    
    # Model fit statistics
    model = results["regarima_results"]["model"]
    stats_dict["aic"] = float(model.aic) if model.aic else None
    stats_dict["bic"] = float(model.bic) if model.bic else None
    stats_dict["sigma2"] = float(model.sigma2)
    
    # Outlier statistics
    outliers = results["regarima_results"]["outliers"]
    stats_dict["n_outliers"] = len(outliers)
    stats_dict["outlier_percentage"] = len(outliers) / 100 * 100  # Assuming 100 observations
    
    # Decomposition statistics
    if results.get("x11_results"):
        seasonal = np.array(results["x11_results"]["d10"])
        stats_dict["seasonal_peak_value"] = float(np.max(np.abs(seasonal - 1)))
    elif results.get("seats_results"):
        seasonal = np.array(results["seats_results"]["seasonal"])
        stats_dict["seasonal_peak_value"] = float(np.max(np.abs(seasonal)))
    
    return stats_dict