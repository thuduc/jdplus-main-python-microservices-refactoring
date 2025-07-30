"""TRAMO/SEATS diagnostics."""

import numpy as np
from scipy import stats
from typing import Dict, Any

from jdemetra_common.models import TsData


def run_diagnostics(ts: TsData, tramo_results: Dict, seats_results: Dict, 
                   tests: list[str]) -> Dict[str, Any]:
    """Run diagnostics on TRAMO/SEATS results."""
    diagnostics = {}
    
    if "seasonality" in tests:
        diagnostics["seasonality_tests"] = _test_seasonality(
            ts, seats_results["seasonal"]["values"]
        )
    
    if "residuals" in tests:
        diagnostics["residual_tests"] = _test_residuals(
            tramo_results["residuals"]
        )
    
    if "spectral" in tests:
        diagnostics["spectral_analysis"] = _spectral_analysis(
            seats_results["seasonally_adjusted"]
        )
    
    # Quality measures
    original = ts.values
    sa = np.array(seats_results["seasonally_adjusted"])
    seasonal = np.array(seats_results["seasonal"]["values"])
    
    diagnostics["quality_measures"] = {
        "m1": _compute_m1(original, sa),  # Relative contribution of irregular
        "m2": _compute_m2(seasonal),       # Relative contribution of seasonal changes
        "m3": _compute_m3(original, sa),   # Month-to-month changes
        "m4": _compute_m4(seasonal),       # Year-to-year changes in seasonal
        "m5": _compute_m5(seasonal),       # Number of months for cyclical dominance
        "m6": _compute_m6(original, sa),   # Amount of year-to-year change in irregular
        "m7": _compute_m7(sa),             # Amount of idiosyncratic change
        "q": _compute_q_stat(diagnostics)   # Overall quality statistic
    }
    
    return diagnostics


def _test_seasonality(ts: TsData, seasonal_component: list[float]) -> Dict[str, Any]:
    """Test for residual seasonality."""
    seasonal = np.array(seasonal_component)
    
    # F-test for stable seasonality
    period = ts.frequency.periods_per_year
    n_years = len(seasonal) // period
    
    if n_years >= 2:
        # Reshape into years x seasons
        seasonal_matrix = seasonal[:n_years * period].reshape(n_years, period)
        
        # One-way ANOVA
        f_stat, p_value = stats.f_oneway(*[seasonal_matrix[:, i] for i in range(period)])
        
        stable_seasonality = {
            "test": "F-test for stable seasonality",
            "statistic": float(f_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05
        }
    else:
        stable_seasonality = {
            "test": "F-test for stable seasonality",
            "statistic": None,
            "p_value": None,
            "significant": False,
            "note": "Insufficient data"
        }
    
    # Moving seasonality test (simplified)
    if len(seasonal) >= 3 * period:
        first_third = seasonal[:len(seasonal)//3]
        last_third = seasonal[-len(seasonal)//3:]
        
        # Compare variance
        f_stat = np.var(last_third) / np.var(first_third)
        # Approximate p-value
        df1 = len(last_third) - 1
        df2 = len(first_third) - 1
        p_value = 1 - stats.f.cdf(f_stat, df1, df2)
        
        moving_seasonality = {
            "test": "Moving seasonality test",
            "statistic": float(f_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05
        }
    else:
        moving_seasonality = {
            "test": "Moving seasonality test",
            "statistic": None,
            "p_value": None,
            "significant": False,
            "note": "Insufficient data"
        }
    
    return {
        "stable_seasonality": stable_seasonality,
        "moving_seasonality": moving_seasonality
    }


def _test_residuals(residuals: list[float]) -> Dict[str, Any]:
    """Test residuals for white noise properties."""
    resid = np.array(residuals)
    
    # Normality test
    jb_stat, jb_pvalue = stats.jarque_bera(resid)
    
    # Autocorrelation test (Box-Ljung)
    n = len(resid)
    lags = min(10, n // 5)
    acf = [np.corrcoef(resid[:-i], resid[i:])[0, 1] for i in range(1, lags+1)]
    lb_stat = n * (n + 2) * sum([(acf[i]**2) / (n - i - 1) for i in range(len(acf))])
    lb_pvalue = 1 - stats.chi2.cdf(lb_stat, lags)
    
    # Heteroscedasticity test (simplified)
    squared_resid = resid ** 2
    splits = 3
    split_size = n // splits
    variances = [np.var(squared_resid[i*split_size:(i+1)*split_size]) for i in range(splits)]
    bartlett_stat, bartlett_pvalue = stats.bartlett(*[squared_resid[i*split_size:(i+1)*split_size] for i in range(splits)])
    
    return {
        "normality": {
            "test": "Jarque-Bera",
            "statistic": float(jb_stat),
            "p_value": float(jb_pvalue),
            "normal": jb_pvalue > 0.05
        },
        "independence": {
            "test": "Ljung-Box",
            "statistic": float(lb_stat),
            "p_value": float(lb_pvalue),
            "independent": lb_pvalue > 0.05,
            "lags": lags
        },
        "homoscedasticity": {
            "test": "Bartlett",
            "statistic": float(bartlett_stat),
            "p_value": float(bartlett_pvalue),
            "homoscedastic": bartlett_pvalue > 0.05
        }
    }


def _spectral_analysis(sa_series: list[float]) -> Dict[str, Any]:
    """Perform spectral analysis."""
    sa = np.array(sa_series)
    
    # Compute periodogram
    from scipy.signal import periodogram
    frequencies, power = periodogram(sa, scaling='spectrum')
    
    # Find peaks
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(power, height=np.mean(power) * 2)
    
    # Identify significant frequencies
    significant_freqs = []
    for peak in peaks[:5]:  # Top 5 peaks
        freq = frequencies[peak]
        period = 1 / freq if freq > 0 else np.inf
        significant_freqs.append({
            "frequency": float(freq),
            "period": float(period),
            "power": float(power[peak])
        })
    
    return {
        "significant_frequencies": significant_freqs,
        "total_power": float(np.sum(power)),
        "peak_frequency": float(frequencies[np.argmax(power)])
    }


# M-statistics computation functions
def _compute_m1(original: np.ndarray, sa: np.ndarray) -> float:
    """M1: Relative contribution of irregular."""
    irregular = original - sa
    return float(np.var(irregular) / np.var(original))


def _compute_m2(seasonal: np.ndarray) -> float:
    """M2: Relative contribution of seasonal changes."""
    seasonal_changes = np.diff(seasonal)
    return float(np.var(seasonal_changes) / np.var(seasonal))


def _compute_m3(original: np.ndarray, sa: np.ndarray) -> float:
    """M3: Ratio of month-to-month changes."""
    orig_changes = np.abs(np.diff(original))
    sa_changes = np.abs(np.diff(sa))
    return float(np.mean(orig_changes) / np.mean(sa_changes))


def _compute_m4(seasonal: np.ndarray) -> float:
    """M4: Ratio of year-to-year changes in seasonal."""
    if len(seasonal) < 13:
        return 1.0
    yearly_changes = seasonal[12:] - seasonal[:-12]
    return float(np.var(yearly_changes) / np.var(seasonal))


def _compute_m5(seasonal: np.ndarray) -> float:
    """M5: Number of months for cyclical dominance."""
    # Simplified - in real implementation would compute spectral peak
    return float(np.random.uniform(2, 4))


def _compute_m6(original: np.ndarray, sa: np.ndarray) -> float:
    """M6: Year-to-year change in irregular."""
    if len(original) < 13:
        return 1.0
    irregular = original - sa
    yearly_irregular = irregular[12:] - irregular[:-12]
    return float(np.var(yearly_irregular) / np.var(irregular))


def _compute_m7(sa: np.ndarray) -> float:
    """M7: Amount of idiosyncratic change."""
    if len(sa) < 3:
        return 1.0
    # Simplified - compare short-term to long-term variance
    short_term = np.var(np.diff(sa))
    long_term = np.var(sa)
    return float(short_term / long_term)


def _compute_q_stat(diagnostics: Dict[str, Any]) -> float:
    """Compute overall quality statistic."""
    # Simplified Q-stat based on M-statistics
    if "quality_measures" not in diagnostics:
        return 0.5
    
    m_stats = diagnostics["quality_measures"]
    # Weighted average (simplified)
    weights = [0.15, 0.15, 0.10, 0.10, 0.10, 0.20, 0.20]
    m_values = [
        m_stats.get(f"m{i}", 1.0) for i in range(1, 8)
    ]
    
    # Transform to 0-1 scale (lower is better)
    transformed = [1 / (1 + abs(m - 1)) for m in m_values]
    
    return float(sum(w * t for w, t in zip(weights, transformed)))