"""ARIMA model definitions."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import numpy as np


@dataclass
class ArimaOrder:
    """ARIMA model order specification."""
    
    p: int  # AR order
    d: int  # Differencing order
    q: int  # MA order
    seasonal_p: int = 0  # Seasonal AR order
    seasonal_d: int = 0  # Seasonal differencing
    seasonal_q: int = 0  # Seasonal MA order
    seasonal_period: int = 0  # Seasonal period
    
    def __post_init__(self):
        """Validate orders."""
        if self.p < 0 or self.d < 0 or self.q < 0:
            raise ValueError("Orders must be non-negative")
        if self.seasonal_p < 0 or self.seasonal_d < 0 or self.seasonal_q < 0:
            raise ValueError("Seasonal orders must be non-negative")
        if self.seasonal_period < 0:
            raise ValueError("Seasonal period must be non-negative")
        
        # If any seasonal component is specified, period must be > 0
        if (self.seasonal_p > 0 or self.seasonal_d > 0 or self.seasonal_q > 0) and self.seasonal_period == 0:
            raise ValueError("Seasonal period must be specified when using seasonal components")
    
    @property
    def is_seasonal(self) -> bool:
        """Check if model has seasonal components."""
        return self.seasonal_period > 0
    
    def to_tuple(self) -> tuple:
        """Convert to tuple representation."""
        if self.is_seasonal:
            return (
                (self.p, self.d, self.q),
                (self.seasonal_p, self.seasonal_d, self.seasonal_q, self.seasonal_period)
            )
        return (self.p, self.d, self.q)
    
    def __str__(self) -> str:
        """String representation."""
        base = f"ARIMA({self.p},{self.d},{self.q})"
        if self.is_seasonal:
            seasonal = f"({self.seasonal_p},{self.seasonal_d},{self.seasonal_q})[{self.seasonal_period}]"
            return f"{base}x{seasonal}"
        return base


@dataclass
class ArimaModel:
    """ARIMA model with estimated parameters."""
    
    order: ArimaOrder
    ar_params: Optional[np.ndarray] = None
    ma_params: Optional[np.ndarray] = None
    seasonal_ar_params: Optional[np.ndarray] = None
    seasonal_ma_params: Optional[np.ndarray] = None
    intercept: float = 0.0
    sigma2: float = 1.0  # Residual variance
    log_likelihood: Optional[float] = None
    aic: Optional[float] = None
    bic: Optional[float] = None
    
    def __post_init__(self):
        """Validate and convert parameters."""
        if self.ar_params is not None:
            self.ar_params = np.asarray(self.ar_params)
            if len(self.ar_params) != self.order.p:
                raise ValueError(f"Expected {self.order.p} AR parameters, got {len(self.ar_params)}")
        
        if self.ma_params is not None:
            self.ma_params = np.asarray(self.ma_params)
            if len(self.ma_params) != self.order.q:
                raise ValueError(f"Expected {self.order.q} MA parameters, got {len(self.ma_params)}")
        
        if self.seasonal_ar_params is not None:
            self.seasonal_ar_params = np.asarray(self.seasonal_ar_params)
            if len(self.seasonal_ar_params) != self.order.seasonal_p:
                raise ValueError(f"Expected {self.order.seasonal_p} seasonal AR parameters")
        
        if self.seasonal_ma_params is not None:
            self.seasonal_ma_params = np.asarray(self.seasonal_ma_params)
            if len(self.seasonal_ma_params) != self.order.seasonal_q:
                raise ValueError(f"Expected {self.order.seasonal_q} seasonal MA parameters")
    
    @property
    def n_parameters(self) -> int:
        """Get total number of parameters."""
        n = 1  # intercept
        n += self.order.p + self.order.q  # AR and MA
        if self.order.is_seasonal:
            n += self.order.seasonal_p + self.order.seasonal_q
        return n
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "order": {
                "p": self.order.p,
                "d": self.order.d,
                "q": self.order.q,
                "seasonal_p": self.order.seasonal_p,
                "seasonal_d": self.order.seasonal_d,
                "seasonal_q": self.order.seasonal_q,
                "seasonal_period": self.order.seasonal_period,
            },
            "ar_params": self.ar_params.tolist() if self.ar_params is not None else None,
            "ma_params": self.ma_params.tolist() if self.ma_params is not None else None,
            "seasonal_ar_params": self.seasonal_ar_params.tolist() if self.seasonal_ar_params is not None else None,
            "seasonal_ma_params": self.seasonal_ma_params.tolist() if self.seasonal_ma_params is not None else None,
            "intercept": self.intercept,
            "sigma2": self.sigma2,
            "log_likelihood": self.log_likelihood,
            "aic": self.aic,
            "bic": self.bic,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArimaModel":
        """Create from dictionary."""
        order = ArimaOrder(**data["order"])
        return cls(
            order=order,
            ar_params=np.array(data["ar_params"]) if data["ar_params"] is not None else None,
            ma_params=np.array(data["ma_params"]) if data["ma_params"] is not None else None,
            seasonal_ar_params=np.array(data["seasonal_ar_params"]) if data["seasonal_ar_params"] is not None else None,
            seasonal_ma_params=np.array(data["seasonal_ma_params"]) if data["seasonal_ma_params"] is not None else None,
            intercept=data["intercept"],
            sigma2=data["sigma2"],
            log_likelihood=data.get("log_likelihood"),
            aic=data.get("aic"),
            bic=data.get("bic"),
        )