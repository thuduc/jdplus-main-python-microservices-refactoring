"""X-13 wrapper (simplified simulation)."""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from statsmodels.tsa.x13 import x13_arima_analysis
from statsmodels.tsa.seasonal import STL
import pandas as pd

from jdemetra_common.models import TsData, ArimaModel, ArimaOrder
from ..schemas.specification import X13Specification


class X13Processor:
    """X-13 processor wrapper."""
    
    def __init__(self, specification: X13Specification):
        self.spec = specification
    
    def process(self, ts: TsData) -> Dict[str, Any]:
        """Process time series with X-13."""
        # In production, would use actual X-13 binary via x13_arima_analysis
        # Here we simulate with statsmodels and custom logic
        
        # Convert to pandas
        series = ts.to_pandas()
        
        # Apply transformation
        transformed, transform_type = self._apply_transformation(series)
        
        # Estimate RegARIMA
        regarima_results = self._estimate_regarima(transformed, ts)
        regarima_results["transformation"] = transform_type
        
        # Perform decomposition
        if self.spec.seats:
            decomposition_results = self._seats_decompose(transformed, regarima_results)
            x11_results = None
        else:
            decomposition_results = None
            x11_results = self._x11_decompose(transformed, ts)
        
        # Generate forecasts
        forecasts = self._generate_forecasts(transformed, regarima_results["model"], self.spec.forecast_maxlead)
        
        return {
            "regarima_results": regarima_results,
            "x11_results": x11_results,
            "seats_results": decomposition_results,
            "forecasts": forecasts,
            "specification_used": self.spec.dict()
        }
    
    def _apply_transformation(self, series: pd.Series) -> Tuple[pd.Series, str]:
        """Apply transformation to series."""
        if self.spec.regarima.transform_function == "log":
            if (series <= 0).any():
                return series, "none"
            return np.log(series), "log"
        elif self.spec.regarima.transform_function == "auto":
            # Simple auto-detection
            cv = series.std() / series.mean()
            if cv > 0.3 and (series > 0).all():
                return np.log(series), "log"
            return series, "none"
        else:
            return series, "none"
    
    def _estimate_regarima(self, series: pd.Series, ts: TsData) -> Dict[str, Any]:
        """Estimate RegARIMA model."""
        # Detect outliers
        outliers = self._detect_outliers(series.values)
        
        # Create regression matrix
        n = len(series)
        X = []
        effect_names = []
        
        # Trading days effect (simplified)
        if "td" in self.spec.regarima.variables:
            # Simulate trading days as day-of-week effect
            td_effect = np.sin(2 * np.pi * np.arange(n) / 7)
            X.append(td_effect)
            effect_names.append("td")
        
        # Easter effect (simplified)
        if "easter" in self.spec.regarima.variables:
            # Simulate Easter as seasonal pulse
            easter_effect = np.zeros(n)
            easter_positions = [i for i in range(n) if i % 12 == 3]  # April
            for pos in easter_positions:
                if pos < n:
                    easter_effect[pos] = 1
            X.append(easter_effect)
            effect_names.append("easter")
        
        # Add outlier regressors
        for outlier in outliers:
            outlier_reg = np.zeros(n)
            outlier_reg[outlier["position"]] = 1
            X.append(outlier_reg)
            effect_names.append(f"{outlier['type']}_{outlier['position']}")
        
        # Estimate ARIMA with regressors
        if self.spec.regarima.model:
            # Use specified model
            if len(self.spec.regarima.model) == 3:
                order = self.spec.regarima.model
                seasonal_order = None
            else:
                order = self.spec.regarima.model[:3]
                seasonal_order = list(self.spec.regarima.model[3:]) + [ts.frequency.periods_per_year]
        else:
            # Auto-select (simplified)
            order = (1, 1, 1)
            seasonal_order = (0, 1, 1, ts.frequency.periods_per_year)
        
        # Create ARIMA model (simplified estimation)
        arima_order = ArimaOrder(
            p=order[0], d=order[1], q=order[2],
            seasonal_p=seasonal_order[0] if seasonal_order else 0,
            seasonal_d=seasonal_order[1] if seasonal_order else 0,
            seasonal_q=seasonal_order[2] if seasonal_order else 0,
            seasonal_period=seasonal_order[3] if seasonal_order else 0
        )
        
        # Simulate parameter estimation
        model = ArimaModel(
            order=arima_order,
            ar_params=np.random.normal(0, 0.3, order[0]) if order[0] > 0 else None,
            ma_params=np.random.normal(0, 0.3, order[2]) if order[2] > 0 else None,
            intercept=float(series.mean()),
            sigma2=float(series.var()),
            aic=1000 + np.random.normal(0, 10),
            bic=1100 + np.random.normal(0, 10)
        )
        
        # Regression effects
        regression_effects = {}
        if X:
            # Simulate regression coefficients
            for i, name in enumerate(effect_names):
                regression_effects[name] = {
                    "coefficient": float(np.random.normal(0, 0.1)),
                    "std_error": float(np.random.uniform(0.01, 0.05)),
                    "t_value": float(np.random.normal(0, 2))
                }
        
        return {
            "model": model,
            "regression_effects": regression_effects,
            "outliers": outliers
        }
    
    def _detect_outliers(self, data: np.ndarray) -> List[Dict[str, Any]]:
        """Detect outliers."""
        outliers = []
        
        # Simple outlier detection
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        threshold = self.spec.regarima.outlier_critical_value * mad * 1.4826
        
        for i in range(len(data)):
            if np.abs(data[i] - median) > threshold:
                outlier_type = "AO" if i == 0 or i == len(data)-1 else "LS"
                if outlier_type == "AO" and "ao" in self.spec.regarima.variables:
                    outliers.append({
                        "position": i,
                        "type": outlier_type,
                        "value": float(data[i]),
                        "t_value": float((data[i] - median) / (mad * 1.4826))
                    })
                elif outlier_type == "LS" and "ls" in self.spec.regarima.variables:
                    outliers.append({
                        "position": i,
                        "type": outlier_type,
                        "value": float(data[i]),
                        "t_value": float((data[i] - median) / (mad * 1.4826))
                    })
        
        return outliers
    
    def _x11_decompose(self, series: pd.Series, ts: TsData) -> Dict[str, Any]:
        """Perform X-11 decomposition (simplified)."""
        # Use STL as approximation
        period = ts.frequency.periods_per_year
        
        if len(series) < 2 * period:
            # Not enough data for decomposition
            n = len(series)
            return {
                "d10": [1.0] * n,  # No seasonal
                "d11": series.tolist(),  # SA = original
                "d12": series.tolist(),  # Trend = original
                "d13": [0.0] * n,  # No irregular
                "decomposition_mode": self.spec.x11.mode
            }
        
        # Perform STL decomposition
        stl = STL(series, period=period, seasonal=13)
        result = stl.fit()
        
        # Map to X-11 components
        if self.spec.x11.mode == "mult":
            # Multiplicative mode
            seasonal_factors = result.seasonal / series.mean() + 1
            sa_series = series / seasonal_factors
            irregular = series / (result.trend * seasonal_factors)
        else:
            # Additive mode
            seasonal_factors = result.seasonal
            sa_series = series - seasonal_factors
            irregular = series - result.trend - seasonal_factors
        
        return {
            "d10": seasonal_factors.tolist(),
            "d11": sa_series.tolist(),
            "d12": result.trend.tolist(),
            "d13": irregular.tolist(),
            "decomposition_mode": self.spec.x11.mode
        }
    
    def _seats_decompose(self, series: pd.Series, regarima_results: Dict) -> Dict[str, Any]:
        """Perform SEATS decomposition (simplified)."""
        # Simplified SEATS using model-based decomposition
        n = len(series)
        
        # Extract trend (simplified)
        from scipy.signal import savgol_filter
        trend = savgol_filter(series.values, min(51, n//4*2+1), 3)
        
        # Extract seasonal
        detrended = series.values - trend
        period = 12  # Assume monthly
        seasonal = np.zeros(n)
        
        for month in range(period):
            month_data = [detrended[i] for i in range(month, n, period)]
            if month_data:
                seasonal[month::period] = np.mean(month_data)
        
        # Center seasonal
        seasonal = seasonal - seasonal.mean()
        
        # Irregular
        irregular = series.values - trend - seasonal
        
        # Seasonally adjusted
        sa = series.values - seasonal
        
        return {
            "trend": trend.tolist(),
            "seasonal": seasonal.tolist(),
            "irregular": irregular.tolist(),
            "seasonally_adjusted": sa.tolist()
        }
    
    def _generate_forecasts(self, series: pd.Series, model: ArimaModel, horizon: int) -> List[Dict[str, Any]]:
        """Generate forecasts."""
        # Simplified forecasting
        last_value = series.iloc[-1]
        forecasts = []
        
        for h in range(1, horizon + 1):
            # Simple random walk with drift
            forecast_value = last_value * (1 + np.random.normal(0, 0.01))
            std_error = np.sqrt(model.sigma2 * h)
            
            forecasts.append({
                "period": h,
                "forecast": float(forecast_value),
                "lower_95": float(forecast_value - 1.96 * std_error),
                "upper_95": float(forecast_value + 1.96 * std_error)
            })
            
            last_value = forecast_value
        
        return forecasts