"""Distribution fitting and testing."""

import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Any


DISTRIBUTION_MAP = {
    "normal": stats.norm,
    "lognormal": stats.lognorm,
    "exponential": stats.expon,
    "gamma": stats.gamma,
    "beta": stats.beta
}


def fit_distribution(data: np.ndarray, distribution_name: str) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Fit a distribution to data.
    
    Returns:
        Tuple of (parameters, goodness_of_fit_metrics)
    """
    if distribution_name not in DISTRIBUTION_MAP:
        raise ValueError(f"Unknown distribution: {distribution_name}")
    
    dist = DISTRIBUTION_MAP[distribution_name]
    
    # Fit distribution
    params = dist.fit(data)
    
    # Extract parameters with meaningful names
    if distribution_name == "normal":
        param_dict = {"loc": params[0], "scale": params[1]}
    elif distribution_name == "lognormal":
        param_dict = {"s": params[0], "loc": params[1], "scale": params[2]}
    elif distribution_name == "exponential":
        param_dict = {"loc": params[0], "scale": params[1]}
    elif distribution_name == "gamma":
        param_dict = {"a": params[0], "loc": params[1], "scale": params[2]}
    elif distribution_name == "beta":
        param_dict = {"a": params[0], "b": params[1], "loc": params[2], "scale": params[3]}
    else:
        param_dict = {f"param_{i}": p for i, p in enumerate(params)}
    
    # Goodness of fit tests
    # Kolmogorov-Smirnov test
    ks_stat, ks_pvalue = stats.kstest(data, lambda x: dist.cdf(x, *params))
    
    # Calculate log-likelihood
    log_likelihood = np.sum(dist.logpdf(data, *params))
    
    # AIC and BIC
    n_params = len(params)
    n_data = len(data)
    aic = 2 * n_params - 2 * log_likelihood
    bic = n_params * np.log(n_data) - 2 * log_likelihood
    
    goodness_metrics = {
        "ks_statistic": float(ks_stat),
        "ks_pvalue": float(ks_pvalue),
        "log_likelihood": float(log_likelihood),
        "aic": float(aic),
        "bic": float(bic)
    }
    
    return param_dict, goodness_metrics


def fit_multiple_distributions(data: np.ndarray, distribution_names: List[str]) -> List[Dict[str, Any]]:
    """
    Fit multiple distributions and rank by goodness of fit.
    
    Returns:
        List of fitting results, sorted by AIC (best first)
    """
    results = []
    
    for dist_name in distribution_names:
        try:
            params, metrics = fit_distribution(data, dist_name)
            results.append({
                "distribution": dist_name,
                "parameters": params,
                "goodness_of_fit": metrics
            })
        except Exception as e:
            # Some distributions might fail to fit
            print(f"Failed to fit {dist_name}: {e}")
            continue
    
    # Sort by AIC (lower is better)
    results.sort(key=lambda x: x["goodness_of_fit"]["aic"])
    
    # Mark best fit
    if results:
        results[0]["best_fit"] = True
        for r in results[1:]:
            r["best_fit"] = False
    
    return results