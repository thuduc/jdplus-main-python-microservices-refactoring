"""Statistical tests implementation."""

import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss, acf, pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from typing import Tuple, Dict, Any, Optional


def normality_test(data: np.ndarray, method: str = "shapiro") -> Tuple[float, float, Dict[str, Any]]:
    """
    Test for normality.
    
    Returns:
        Tuple of (statistic, p_value, additional_info)
    """
    if method == "shapiro":
        stat, p_value = stats.shapiro(data)
        info = {"method": "Shapiro-Wilk"}
    elif method == "jarque_bera":
        stat, p_value = stats.jarque_bera(data)
        info = {"method": "Jarque-Bera"}
    elif method == "anderson":
        result = stats.anderson(data, dist='norm')
        stat = result.statistic
        # Use 5% critical value for p-value approximation
        critical_val = result.critical_values[2]  # 5% level
        p_value = 0.05 if stat > critical_val else 0.95
        info = {
            "method": "Anderson-Darling",
            "critical_values": dict(zip(result.significance_level, result.critical_values))
        }
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return stat, p_value, info


def stationarity_test(data: np.ndarray, method: str = "adf", regression: str = "c", 
                     max_lag: Optional[int] = None) -> Tuple[float, float, Dict[str, Any]]:
    """
    Test for stationarity.
    
    Returns:
        Tuple of (statistic, p_value, additional_info)
    """
    if method == "adf":
        # Augmented Dickey-Fuller test
        result = adfuller(data, regression=regression, maxlag=max_lag, autolag='AIC' if max_lag is None else None)
        stat, p_value = result[0], result[1]
        info = {
            "method": "Augmented Dickey-Fuller",
            "lags_used": result[2],
            "n_obs": result[3],
            "critical_values": result[4],
            "null_hypothesis": "Unit root (non-stationary)"
        }
    elif method == "kpss":
        # KPSS test
        stat, p_value, lags, crit = kpss(data, regression=regression, nlags=max_lag)
        info = {
            "method": "KPSS",
            "lags_used": lags,
            "critical_values": crit,
            "null_hypothesis": "Stationary"
        }
    elif method == "pp":
        # Phillips-Perron test (using ADF with lag=0 as approximation)
        result = adfuller(data, regression=regression, maxlag=0)
        stat, p_value = result[0], result[1]
        info = {
            "method": "Phillips-Perron (approximated)",
            "critical_values": result[4],
            "null_hypothesis": "Unit root (non-stationary)"
        }
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return stat, p_value, info


def randomness_test(data: np.ndarray, method: str = "runs", lags: int = 10) -> Tuple[float, float, Dict[str, Any]]:
    """
    Test for randomness.
    
    Returns:
        Tuple of (statistic, p_value, additional_info)
    """
    if method == "runs":
        # Runs test
        median = np.median(data)
        runs, n1, n2 = 0, 0, 0
        
        # Convert to binary sequence based on median
        for i in range(len(data)):
            if data[i] >= median:
                n1 += 1
            else:
                n2 += 1
            
            if i > 0:
                if (data[i] >= median and data[i-1] < median) or \
                   (data[i] < median and data[i-1] >= median):
                    runs += 1
        
        runs += 1  # Add one for the first run
        
        # Expected runs and variance
        expected_runs = (2 * n1 * n2) / (n1 + n2) + 1
        variance = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / \
                   ((n1 + n2) ** 2 * (n1 + n2 - 1))
        
        # Z-statistic
        if variance > 0:
            z_stat = (runs - expected_runs) / np.sqrt(variance)
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            z_stat = 0
            p_value = 1.0
        
        info = {
            "method": "Runs test",
            "n_runs": runs,
            "expected_runs": expected_runs,
            "n_above_median": n1,
            "n_below_median": n2
        }
        
        return z_stat, p_value, info
        
    elif method in ["ljung_box", "box_pierce"]:
        # Ljung-Box or Box-Pierce test
        result = acorr_ljungbox(data, lags=lags, boxpierce=(method == "box_pierce"), return_df=False)
        
        if method == "box_pierce":
            stat = result[2][-1]  # Box-Pierce statistic at max lag
            p_value = result[3][-1]  # Box-Pierce p-value at max lag
        else:
            stat = result[0][-1]  # Ljung-Box statistic at max lag
            p_value = result[1][-1]  # Ljung-Box p-value at max lag
        
        info = {
            "method": "Ljung-Box" if method == "ljung_box" else "Box-Pierce",
            "lags": lags,
            "null_hypothesis": "No autocorrelation"
        }
        
        return stat, p_value, info
    
    else:
        raise ValueError(f"Unknown method: {method}")


def seasonality_test(data: np.ndarray, period: int, method: str = "auto") -> Tuple[float, float, Dict[str, Any]]:
    """
    Test for seasonality.
    
    Returns:
        Tuple of (statistic, p_value, additional_info)
    """
    n = len(data)
    n_periods = n // period
    
    if n_periods < 2:
        raise ValueError(f"Not enough data for seasonality test with period {period}")
    
    # Reshape data into seasonal periods
    truncated_data = data[:n_periods * period]
    seasonal_matrix = truncated_data.reshape(n_periods, period)
    
    if method == "auto":
        # Choose method based on data characteristics
        if n_periods < 10:
            method = "friedman"
        else:
            method = "kruskal"
    
    if method == "kruskal":
        # Kruskal-Wallis test across periods
        groups = [seasonal_matrix[:, i] for i in range(period)]
        stat, p_value = stats.kruskal(*groups)
        info = {
            "method": "Kruskal-Wallis",
            "null_hypothesis": "No seasonal differences",
            "n_periods": n_periods,
            "period": period
        }
        
    elif method == "friedman":
        # Friedman test
        stat, p_value = stats.friedmanchisquare(*[seasonal_matrix[:, i] for i in range(period)])
        info = {
            "method": "Friedman",
            "null_hypothesis": "No seasonal differences",
            "n_periods": n_periods,
            "period": period
        }
        
    elif method == "qs":
        # QS (Seasonal Ljung-Box) test
        # Compute autocorrelations at seasonal lags
        acf_vals = acf(data, nlags=period * 4, fft=True)
        seasonal_lags = np.arange(period, len(acf_vals), period)
        seasonal_acf = acf_vals[seasonal_lags]
        
        # QS statistic
        n = len(data)
        qs_stat = n * (n + 2) * np.sum(seasonal_acf**2 / (n - seasonal_lags))
        df = len(seasonal_lags)
        p_value = 1 - stats.chi2.cdf(qs_stat, df)
        
        info = {
            "method": "QS (Seasonal Ljung-Box)",
            "null_hypothesis": "No seasonal autocorrelation",
            "seasonal_lags_tested": len(seasonal_lags),
            "period": period
        }
        stat = qs_stat
        
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return stat, p_value, info