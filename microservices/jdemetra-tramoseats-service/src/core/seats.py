"""SEATS implementation (simplified)."""

import numpy as np
from scipy import signal
from typing import Dict, Any, List

from jdemetra_common.models import TsData, ArimaModel


class SeatsDecomposer:
    """SEATS decomposer for signal extraction."""
    
    def __init__(self, specification):
        self.spec = specification
    
    def decompose(self, ts: TsData, tramo_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform SEATS decomposition."""
        data = ts.values
        model = tramo_results["model"]
        
        # Apply transformation if needed
        if tramo_results["transform_info"]["type"] == "log":
            data = np.log(data)
        
        # Simplified decomposition using filters
        # In real SEATS, would use ARIMA-model-based decomposition
        
        # Extract components
        trend = self._extract_trend(data)
        seasonal = self._extract_seasonal(data, ts.frequency.periods_per_year)
        irregular = data - trend - seasonal
        seasonally_adjusted = data - seasonal
        
        # Back-transform if needed
        if tramo_results["transform_info"]["type"] == "log":
            trend = np.exp(trend)
            seasonal = np.exp(seasonal) - 1  # Multiplicative seasonal
            irregular = np.exp(irregular) - 1
            seasonally_adjusted = np.exp(seasonally_adjusted)
        
        return {
            "trend": {
                "name": "trend",
                "values": trend.tolist(),
                "properties": {
                    "variance": float(np.var(trend)),
                    "contribution": float(np.var(trend) / np.var(data))
                }
            },
            "seasonal": {
                "name": "seasonal",
                "values": seasonal.tolist(),
                "properties": {
                    "variance": float(np.var(seasonal)),
                    "contribution": float(np.var(seasonal) / np.var(data)),
                    "period": ts.frequency.periods_per_year
                }
            },
            "irregular": {
                "name": "irregular",
                "values": irregular.tolist(),
                "properties": {
                    "variance": float(np.var(irregular)),
                    "contribution": float(np.var(irregular) / np.var(data))
                }
            },
            "seasonally_adjusted": seasonally_adjusted.tolist()
        }
    
    def _extract_trend(self, data: np.ndarray) -> np.ndarray:
        """Extract trend component using Henderson filter."""
        # Simplified trend extraction
        # Real SEATS would use ARIMA-model-based Wiener-Kolmogorov filter
        
        # Henderson filter (simplified)
        window_length = min(13, len(data) // 4)
        if window_length % 2 == 0:
            window_length += 1
        
        # Apply moving average
        trend = np.convolve(data, np.ones(window_length)/window_length, mode='same')
        
        # Handle boundaries
        for i in range(window_length//2):
            trend[i] = data[i]
            trend[-(i+1)] = data[-(i+1)]
        
        return trend
    
    def _extract_seasonal(self, data: np.ndarray, period: int) -> np.ndarray:
        """Extract seasonal component."""
        # Simplified seasonal extraction
        # Real SEATS would use ARIMA-model-based extraction
        
        n = len(data)
        seasonal = np.zeros(n)
        
        # Calculate seasonal means
        seasonal_means = []
        for season in range(period):
            season_data = [data[i] for i in range(season, n, period)]
            if season_data:
                seasonal_means.append(np.mean(season_data))
            else:
                seasonal_means.append(0)
        
        # Center seasonal means
        mean_of_means = np.mean(seasonal_means)
        seasonal_means = [s - mean_of_means for s in seasonal_means]
        
        # Apply seasonal pattern
        for i in range(n):
            seasonal[i] = seasonal_means[i % period]
        
        # Smooth seasonal component
        if n > 2 * period:
            # Apply simple smoothing
            smooth_seasonal = np.zeros(n)
            for i in range(period, n - period):
                smooth_seasonal[i] = np.mean([seasonal[j] for j in range(i-period//2, i+period//2+1)])
            
            # Blend smoothed with original at boundaries
            for i in range(period):
                weight = i / period
                smooth_seasonal[i] = (1 - weight) * seasonal[i] + weight * smooth_seasonal[period]
                smooth_seasonal[-(i+1)] = (1 - weight) * seasonal[-(i+1)] + weight * smooth_seasonal[-(period+1)]
            
            seasonal = smooth_seasonal
        
        return seasonal