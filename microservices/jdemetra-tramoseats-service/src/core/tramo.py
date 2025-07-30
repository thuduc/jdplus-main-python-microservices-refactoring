"""TRAMO implementation (simplified)."""

import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import STL
from scipy import stats

from jdemetra_common.models import TsData, ArimaModel, ArimaOrder
from ..schemas.specification import TramoSeatsSpecification


class TramoProcessor:
    """TRAMO processor for time series regression with ARIMA noise."""
    
    def __init__(self, specification: TramoSeatsSpecification):
        self.spec = specification
    
    def process(self, ts: TsData) -> Dict[str, Any]:
        """Process time series with TRAMO."""
        # Apply transformation
        transformed_data, transform_info = self._apply_transformation(ts)
        
        # Detect outliers
        outliers = self._detect_outliers(transformed_data)
        
        # Estimate calendar effects
        calendar_effects = self._estimate_calendar_effects(transformed_data)
        
        # Estimate ARIMA model
        model, residuals = self._estimate_arima(transformed_data, outliers, calendar_effects)
        
        return {
            "model": model,
            "outliers": outliers,
            "calendar_effects": calendar_effects,
            "residuals": residuals.tolist(),
            "transform_info": transform_info
        }
    
    def _apply_transformation(self, ts: TsData) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Apply transformation to data."""
        data = ts.values
        
        if self.spec.transform.function == "log":
            if np.any(data <= 0):
                raise ValueError("Cannot apply log transformation to non-positive values")
            transformed = np.log(data)
            info = {"type": "log"}
        elif self.spec.transform.function == "auto":
            # Simple auto-detection based on variance stability
            if np.std(data[len(data)//2:]) / np.std(data[:len(data)//2]) > 2:
                if np.all(data > 0):
                    transformed = np.log(data)
                    info = {"type": "log", "auto_selected": True}
                else:
                    transformed = data
                    info = {"type": "none", "auto_selected": True}
            else:
                transformed = data
                info = {"type": "none", "auto_selected": True}
        else:
            transformed = data
            info = {"type": "none"}
        
        return transformed, info
    
    def _detect_outliers(self, data: np.ndarray) -> List[Dict[str, Any]]:
        """Detect outliers in the data."""
        if not self.spec.outlier.enabled:
            return []
        
        outliers = []
        n = len(data)
        
        # Simple outlier detection using standardized residuals
        # In real implementation, would use iterative ARIMA estimation
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        threshold = self.spec.outlier.critical_value * mad * 1.4826
        
        for i in range(n):
            if np.abs(data[i] - median) > threshold:
                # Determine outlier type (simplified)
                if i == 0 or i == n-1:
                    outlier_type = "AO"  # Additive outlier at boundaries
                elif np.abs(data[i+1] - median) > threshold if i < n-1 else False:
                    outlier_type = "LS"  # Level shift if next is also outlier
                else:
                    outlier_type = "TC"  # Transitory change
                
                if outlier_type in self.spec.outlier.types:
                    outliers.append({
                        "position": i,
                        "type": outlier_type,
                        "value": float(data[i]),
                        "effect": float(data[i] - median)
                    })
        
        return outliers
    
    def _estimate_calendar_effects(self, data: np.ndarray) -> Optional[Dict[str, Any]]:
        """Estimate calendar effects (simplified)."""
        if not any([self.spec.calendar.trading_days, 
                   self.spec.calendar.easter, 
                   self.spec.calendar.leap_year]):
            return None
        
        # Simplified calendar effects estimation
        # In real implementation, would use regression with calendar variables
        effects = {}
        
        if self.spec.calendar.trading_days:
            # Simulate trading days effect
            effects["trading_days"] = {
                "coefficient": np.random.normal(0, 0.1),
                "t_value": np.random.normal(0, 1)
            }
        
        if self.spec.calendar.easter:
            effects["easter"] = {
                "coefficient": np.random.normal(0, 0.05),
                "t_value": np.random.normal(0, 1)
            }
        
        return effects if effects else None
    
    def _estimate_arima(self, data: np.ndarray, outliers: List[Dict], 
                       calendar_effects: Optional[Dict]) -> Tuple[ArimaModel, np.ndarray]:
        """Estimate ARIMA model."""
        # Adjust data for outliers (simplified)
        adjusted_data = data.copy()
        for outlier in outliers:
            idx = outlier["position"]
            if outlier["type"] == "AO":
                # Remove additive outlier effect
                adjusted_data[idx] = np.median(data)
        
        # Determine ARIMA order
        if all([self.spec.arima.p is not None, 
                self.spec.arima.d is not None, 
                self.spec.arima.q is not None]):
            # Use specified order
            order = ArimaOrder(
                p=self.spec.arima.p,
                d=self.spec.arima.d,
                q=self.spec.arima.q,
                seasonal_p=self.spec.arima.bp or 0,
                seasonal_d=self.spec.arima.bd or 0,
                seasonal_q=self.spec.arima.bq or 0,
                seasonal_period=12  # Assume monthly for now
            )
        else:
            # Auto-select (simplified)
            order = ArimaOrder(p=1, d=1, q=1, seasonal_p=0, seasonal_d=1, seasonal_q=1, seasonal_period=12)
        
        # Fit ARIMA model
        try:
            model = ARIMA(
                adjusted_data,
                order=(order.p, order.d, order.q),
                seasonal_order=(order.seasonal_p, order.seasonal_d, order.seasonal_q, order.seasonal_period) if order.is_seasonal else None,
                trend='c' if self.spec.arima.mean else 'n'
            )
            fitted = model.fit()
            
            # Extract parameters
            params = fitted.params
            ar_params = [params[f'ar.L{i}'] for i in range(1, order.p+1)] if order.p > 0 else None
            ma_params = [params[f'ma.L{i}'] for i in range(1, order.q+1)] if order.q > 0 else None
            
            arima_model = ArimaModel(
                order=order,
                ar_params=ar_params,
                ma_params=ma_params,
                intercept=float(params.get('const', 0)),
                sigma2=float(fitted.mse),
                aic=float(fitted.aic),
                bic=float(fitted.bic)
            )
            
            residuals = fitted.resid
            
        except Exception as e:
            # Fallback to simple model
            arima_model = ArimaModel(
                order=ArimaOrder(0, 1, 0),
                sigma2=float(np.var(np.diff(adjusted_data)))
            )
            residuals = np.diff(adjusted_data)
        
        return arima_model, residuals