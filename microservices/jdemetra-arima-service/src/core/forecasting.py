"""ARIMA forecasting logic."""

import time
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from typing import List, Tuple

from jdemetra_common.models import TsData, ArimaModel, TsPeriod


def generate_forecasts(ts: TsData, model: ArimaModel, horizon: int, 
                      confidence_level: float = 0.95) -> Tuple[List[dict], float]:
    """
    Generate forecasts from ARIMA model.
    
    Returns:
        Tuple of (forecasts, forecast_time)
    """
    start_time = time.time()
    
    # Convert to pandas
    series = ts.to_pandas()
    
    # Rebuild ARIMA model
    arima_order = (model.order.p, model.order.d, model.order.q)
    if model.order.is_seasonal:
        seasonal_order = (
            model.order.seasonal_p,
            model.order.seasonal_d,
            model.order.seasonal_q,
            model.order.seasonal_period
        )
    else:
        seasonal_order = None
    
    # Create and fit model
    arima = ARIMA(
        series,
        order=arima_order,
        seasonal_order=seasonal_order,
        trend='c' if model.intercept != 0 else 'n'
    )
    
    # Set parameters directly (skip re-estimation)
    # This is a simplified approach - in production would need proper parameter mapping
    fitted = arima.fit()
    
    # Generate forecasts
    forecast_result = fitted.forecast(steps=horizon, alpha=1-confidence_level)
    
    # Get point forecasts and intervals
    if hasattr(forecast_result, 'values'):
        point_forecasts = forecast_result.values
    else:
        point_forecasts = forecast_result
    
    # Get prediction intervals
    forecast_df = fitted.get_forecast(steps=horizon).summary_frame(alpha=1-confidence_level)
    
    # Build forecast list
    forecasts = []
    current_period = ts.end_period
    
    for i in range(horizon):
        # Calculate next period
        if ts.frequency.value == "M":
            if current_period.period == 12:
                next_period = TsPeriod(
                    year=current_period.year + 1,
                    period=1,
                    frequency=ts.frequency
                )
            else:
                next_period = TsPeriod(
                    year=current_period.year,
                    period=current_period.period + 1,
                    frequency=ts.frequency
                )
        elif ts.frequency.value == "Q":
            if current_period.period == 4:
                next_period = TsPeriod(
                    year=current_period.year + 1,
                    period=1,
                    frequency=ts.frequency
                )
            else:
                next_period = TsPeriod(
                    year=current_period.year,
                    period=current_period.period + 1,
                    frequency=ts.frequency
                )
        elif ts.frequency.value == "Y":
            next_period = TsPeriod(
                year=current_period.year + 1,
                period=1,
                frequency=ts.frequency
            )
        else:
            # For other frequencies, simplified increment
            next_period = TsPeriod(
                year=current_period.year,
                period=current_period.period + 1,
                frequency=ts.frequency
            )
        
        # Create forecast point
        forecast_point = {
            "period": {
                "year": next_period.year,
                "period": next_period.period,
                "frequency": next_period.frequency.value
            },
            "forecast": float(forecast_df.iloc[i]['mean']),
            "lower_bound": float(forecast_df.iloc[i][f'mean_ci_lower']),
            "upper_bound": float(forecast_df.iloc[i][f'mean_ci_upper'])
        }
        
        forecasts.append(forecast_point)
        current_period = next_period
    
    forecast_time = time.time() - start_time
    
    return forecasts, forecast_time