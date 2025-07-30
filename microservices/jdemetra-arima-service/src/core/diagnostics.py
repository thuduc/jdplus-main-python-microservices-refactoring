"""ARIMA model diagnostics."""

import numpy as np
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
from statsmodels.tsa.arima.model import ARIMA
from typing import List, Dict, Any

from jdemetra_common.models import TsData, ArimaModel


def run_diagnostics(ts: TsData, model: ArimaModel, tests: List[str]) -> Dict[str, Any]:
    """
    Run diagnostic tests on ARIMA model.
    
    Returns:
        Dictionary of diagnostic results
    """
    # Get residuals
    series = ts.to_pandas()
    
    # Rebuild and fit model to get residuals
    arima_order = (model.order.p, model.order.d, model.order.q)
    seasonal_order = None
    if model.order.is_seasonal:
        seasonal_order = (
            model.order.seasonal_p,
            model.order.seasonal_d,
            model.order.seasonal_q,
            model.order.seasonal_period
        )
    
    arima = ARIMA(
        series,
        order=arima_order,
        seasonal_order=seasonal_order,
        trend='c' if model.intercept != 0 else 'n'
    )
    fitted = arima.fit()
    residuals = fitted.resid
    
    # Residual statistics
    residual_stats = {
        "mean": float(np.mean(residuals)),
        "std": float(np.std(residuals)),
        "skewness": float(stats.skew(residuals)),
        "kurtosis": float(stats.kurtosis(residuals))
    }
    
    # Run requested tests
    test_results = []
    
    if "ljung_box" in tests:
        # Ljung-Box test for residual autocorrelation
        lb_result = acorr_ljungbox(residuals, lags=min(10, len(residuals)//5), return_df=False)
        lb_stat = lb_result[0][-1]  # Last lag
        lb_pvalue = lb_result[1][-1]
        
        test_results.append({
            "test_name": "Ljung-Box",
            "statistic": float(lb_stat),
            "p_value": float(lb_pvalue),
            "conclusion": "No residual autocorrelation" if lb_pvalue > 0.05 else "Residual autocorrelation detected",
            "details": {"lags_tested": len(lb_result[0])}
        })
    
    if "jarque_bera" in tests:
        # Jarque-Bera test for normality
        jb_stat, jb_pvalue = stats.jarque_bera(residuals)
        
        test_results.append({
            "test_name": "Jarque-Bera",
            "statistic": float(jb_stat),
            "p_value": float(jb_pvalue),
            "conclusion": "Residuals are normally distributed" if jb_pvalue > 0.05 else "Residuals are not normally distributed",
            "details": None
        })
    
    if "heteroscedasticity" in tests:
        # Breusch-Pagan test for heteroscedasticity
        # Need to get fitted values
        fitted_values = fitted.fittedvalues
        
        try:
            # Simple heteroscedasticity test using squared residuals
            squared_resid = residuals ** 2
            corr, pvalue = stats.pearsonr(fitted_values, squared_resid)
            
            test_results.append({
                "test_name": "Heteroscedasticity (simplified)",
                "statistic": float(corr),
                "p_value": float(pvalue),
                "conclusion": "No heteroscedasticity" if pvalue > 0.05 else "Heteroscedasticity detected",
                "details": {"method": "correlation_test"}
            })
        except Exception:
            # Fallback if test fails
            test_results.append({
                "test_name": "Heteroscedasticity",
                "statistic": None,
                "p_value": None,
                "conclusion": "Test could not be performed",
                "details": {"error": "Insufficient data or computation error"}
            })
    
    # Overall adequacy assessment
    adequacy_issues = []
    
    for test in test_results:
        if test["p_value"] is not None and test["p_value"] < 0.05:
            adequacy_issues.append(test["test_name"])
    
    if not adequacy_issues:
        model_adequacy = "Model appears adequate based on diagnostic tests"
    else:
        model_adequacy = f"Model shows issues in: {', '.join(adequacy_issues)}"
    
    return {
        "residual_stats": residual_stats,
        "diagnostic_tests": test_results,
        "model_adequacy": model_adequacy
    }