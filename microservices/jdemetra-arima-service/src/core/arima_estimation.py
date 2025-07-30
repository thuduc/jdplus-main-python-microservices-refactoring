"""ARIMA model estimation logic."""

import time
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from pmdarima import auto_arima
from typing import Tuple, Dict, Any, Optional

from jdemetra_common.models import TsData, ArimaModel, ArimaOrder


def estimate_arima(ts: TsData, order: Optional[ArimaOrder] = None, 
                  method: str = "css-mle", include_mean: bool = True) -> Tuple[ArimaModel, Dict[str, Any]]:
    """
    Estimate ARIMA model.
    
    Returns:
        Tuple of (model, fitting_info)
    """
    start_time = time.time()
    
    # Convert to pandas for statsmodels
    series = ts.to_pandas()
    
    # Build ARIMA specification
    if order:
        arima_order = (order.p, order.d, order.q)
        seasonal_order = (order.seasonal_p, order.seasonal_d, order.seasonal_q, order.seasonal_period) \
                        if order.is_seasonal else None
    else:
        # Use auto_arima for automatic selection
        auto_model = auto_arima(
            series,
            start_p=0, start_q=0, max_p=5, max_q=5,
            seasonal=True, m=ts.frequency.periods_per_year,
            stepwise=True, trace=False,
            error_action='ignore',
            suppress_warnings=True
        )
        arima_order = auto_model.order
        seasonal_order = auto_model.seasonal_order if hasattr(auto_model, 'seasonal_order') else None
        
        # Create order object
        if seasonal_order:
            order = ArimaOrder(
                p=arima_order[0], d=arima_order[1], q=arima_order[2],
                seasonal_p=seasonal_order[0], seasonal_d=seasonal_order[1],
                seasonal_q=seasonal_order[2], seasonal_period=seasonal_order[3]
            )
        else:
            order = ArimaOrder(p=arima_order[0], d=arima_order[1], q=arima_order[2])
    
    # Fit model using statsmodels
    if seasonal_order:
        model = ARIMA(
            series, 
            order=arima_order,
            seasonal_order=seasonal_order,
            trend='c' if include_mean else 'n'
        )
    else:
        model = ARIMA(
            series,
            order=arima_order,
            trend='c' if include_mean else 'n'
        )
    
    # Fit the model
    try:
        fitted = model.fit(method=method)
    except Exception as e:
        # Fallback to CSS if MLE fails
        if method == "css-mle":
            fitted = model.fit(method="css")
        else:
            raise e
    
    # Extract parameters
    params = fitted.params
    ar_params = None
    ma_params = None
    seasonal_ar_params = None
    seasonal_ma_params = None
    intercept = 0.0
    
    # Parse parameters based on model specification
    param_names = list(params.index)
    param_values = params.values
    
    # Extract AR parameters
    ar_indices = [i for i, name in enumerate(param_names) if name.startswith('ar.')]
    if ar_indices:
        ar_params = param_values[ar_indices]
    
    # Extract MA parameters
    ma_indices = [i for i, name in enumerate(param_names) if name.startswith('ma.')]
    if ma_indices:
        ma_params = param_values[ma_indices]
    
    # Extract seasonal parameters
    if order.is_seasonal:
        sar_indices = [i for i, name in enumerate(param_names) if name.startswith('ar.S.')]
        if sar_indices:
            seasonal_ar_params = param_values[sar_indices]
        
        sma_indices = [i for i, name in enumerate(param_names) if name.startswith('ma.S.')]
        if sma_indices:
            seasonal_ma_params = param_values[sma_indices]
    
    # Extract intercept
    if 'const' in param_names or 'intercept' in param_names:
        const_idx = param_names.index('const' if 'const' in param_names else 'intercept')
        intercept = param_values[const_idx]
    
    # Create model object
    arima_model = ArimaModel(
        order=order,
        ar_params=ar_params,
        ma_params=ma_params,
        seasonal_ar_params=seasonal_ar_params,
        seasonal_ma_params=seasonal_ma_params,
        intercept=float(intercept),
        sigma2=float(fitted.mse),
        log_likelihood=float(fitted.llf) if hasattr(fitted, 'llf') else None,
        aic=float(fitted.aic),
        bic=float(fitted.bic)
    )
    
    # Fitting information
    fitting_info = {
        "fit_time": time.time() - start_time,
        "method_used": method,
        "convergence": {
            "converged": fitted.mle_retvals['converged'] if hasattr(fitted, 'mle_retvals') else True,
            "iterations": fitted.mle_retvals.get('iterations', 0) if hasattr(fitted, 'mle_retvals') else 0
        },
        "in_sample_metrics": {
            "mse": float(fitted.mse),
            "mae": float(fitted.mae),
            "aic": float(fitted.aic),
            "bic": float(fitted.bic),
            "hqic": float(fitted.hqic) if hasattr(fitted, 'hqic') else None
        }
    }
    
    return arima_model, fitting_info


def identify_arima(ts: TsData, seasonal: bool = True, stepwise: bool = True,
                  max_p: int = 5, max_q: int = 5, max_d: int = 2,
                  information_criterion: str = "aic") -> Tuple[ArimaModel, Dict[str, Any]]:
    """
    Automatically identify best ARIMA model.
    
    Returns:
        Tuple of (best_model, search_info)
    """
    start_time = time.time()
    
    # Convert to pandas
    series = ts.to_pandas()
    
    # Run auto_arima
    auto_model = auto_arima(
        series,
        start_p=0, start_q=0, max_p=max_p, max_q=max_q, max_d=max_d,
        seasonal=seasonal, m=ts.frequency.periods_per_year if seasonal else None,
        stepwise=stepwise,
        information_criterion=information_criterion,
        trace=True,  # Get search details
        error_action='ignore',
        suppress_warnings=True,
        return_valid_fits=True
    )
    
    # Extract order
    arima_order = auto_model.order
    seasonal_order = auto_model.seasonal_order if hasattr(auto_model, 'seasonal_order') else None
    
    if seasonal_order:
        order = ArimaOrder(
            p=arima_order[0], d=arima_order[1], q=arima_order[2],
            seasonal_p=seasonal_order[0], seasonal_d=seasonal_order[1],
            seasonal_q=seasonal_order[2], seasonal_period=seasonal_order[3]
        )
    else:
        order = ArimaOrder(p=arima_order[0], d=arima_order[1], q=arima_order[2])
    
    # Get fitted parameters
    params = auto_model.params()
    
    # Extract parameters (simplified - pmdarima has different structure)
    ar_params = params[:order.p] if order.p > 0 else None
    ma_params = params[order.p:order.p+order.q] if order.q > 0 else None
    
    # Create model
    best_model = ArimaModel(
        order=order,
        ar_params=ar_params,
        ma_params=ma_params,
        intercept=float(params[-1]) if len(params) > order.p + order.q else 0.0,
        sigma2=float(auto_model.sigma2()),
        aic=float(auto_model.aic()),
        bic=float(auto_model.bic()) if hasattr(auto_model, 'bic') else None
    )
    
    # Search information
    search_info = {
        "identification_time": time.time() - start_time,
        "search_summary": {
            "stepwise": stepwise,
            "information_criterion": information_criterion,
            "seasonal_tested": seasonal,
            "max_order": {"p": max_p, "d": max_d, "q": max_q}
        },
        "candidates_evaluated": len(auto_model.valid_fits) if hasattr(auto_model, 'valid_fits') else 1
    }
    
    return best_model, search_info