"""Time series data models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

import numpy as np
import pandas as pd


class TsFrequency(str, Enum):
    """Time series frequency enumeration."""
    
    YEARLY = "Y"
    QUARTERLY = "Q"
    MONTHLY = "M"
    WEEKLY = "W"
    DAILY = "D"
    HOURLY = "H"
    
    @property
    def periods_per_year(self) -> int:
        """Get number of periods per year for this frequency."""
        mapping = {
            "Y": 1,
            "Q": 4,
            "M": 12,
            "W": 52,
            "D": 365,
            "H": 8760,
        }
        return mapping[self.value]


@dataclass
class TsPeriod:
    """Represents a time period."""
    
    year: int
    period: int
    frequency: TsFrequency
    
    def to_datetime(self) -> datetime:
        """Convert to datetime."""
        if self.frequency == TsFrequency.YEARLY:
            return datetime(self.year, 1, 1)
        elif self.frequency == TsFrequency.QUARTERLY:
            month = (self.period - 1) * 3 + 1
            return datetime(self.year, month, 1)
        elif self.frequency == TsFrequency.MONTHLY:
            return datetime(self.year, self.period, 1)
        else:
            raise NotImplementedError(f"Conversion not implemented for {self.frequency}")
    
    def __str__(self) -> str:
        """String representation."""
        if self.frequency == TsFrequency.YEARLY:
            return str(self.year)
        elif self.frequency == TsFrequency.QUARTERLY:
            return f"{self.year}Q{self.period}"
        elif self.frequency == TsFrequency.MONTHLY:
            return f"{self.year}-{self.period:02d}"
        else:
            return f"{self.year}:{self.period}"


@dataclass
class TsData:
    """Time series data container."""
    
    values: np.ndarray
    start_period: TsPeriod
    frequency: TsFrequency
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate data after initialization."""
        self.values = np.asarray(self.values, dtype=np.float64)
        if self.values.ndim != 1:
            raise ValueError("Values must be 1-dimensional")
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def length(self) -> int:
        """Get length of the time series."""
        return len(self.values)
    
    @property
    def end_period(self) -> TsPeriod:
        """Get the end period of the time series."""
        periods_elapsed = self.length - 1
        if self.frequency == TsFrequency.YEARLY:
            return TsPeriod(
                year=self.start_period.year + periods_elapsed,
                period=1,
                frequency=self.frequency
            )
        elif self.frequency == TsFrequency.QUARTERLY:
            total_quarters = (self.start_period.year * 4 + self.start_period.period - 1) + periods_elapsed
            year = total_quarters // 4
            quarter = (total_quarters % 4) + 1
            return TsPeriod(year=year, period=quarter, frequency=self.frequency)
        elif self.frequency == TsFrequency.MONTHLY:
            total_months = (self.start_period.year * 12 + self.start_period.period - 1) + periods_elapsed
            year = total_months // 12
            month = (total_months % 12) + 1
            return TsPeriod(year=year, period=month, frequency=self.frequency)
        else:
            raise NotImplementedError(f"End period calculation not implemented for {self.frequency}")
    
    def to_pandas(self) -> pd.Series:
        """Convert to pandas Series."""
        dates = self._generate_date_index()
        return pd.Series(self.values, index=dates, name="value")
    
    def _generate_date_index(self) -> pd.DatetimeIndex:
        """Generate pandas DatetimeIndex for the time series."""
        start_date = self.start_period.to_datetime()
        freq_map = {
            TsFrequency.YEARLY: "YS",
            TsFrequency.QUARTERLY: "QS",
            TsFrequency.MONTHLY: "MS",
            TsFrequency.WEEKLY: "W",
            TsFrequency.DAILY: "D",
            TsFrequency.HOURLY: "H",
        }
        return pd.date_range(
            start=start_date,
            periods=self.length,
            freq=freq_map[self.frequency]
        )
    
    @classmethod
    def from_pandas(cls, series: pd.Series, frequency: TsFrequency) -> "TsData":
        """Create from pandas Series."""
        if not isinstance(series.index, pd.DatetimeIndex):
            raise ValueError("Series must have DatetimeIndex")
        
        start_date = series.index[0]
        start_period = TsPeriod(
            year=start_date.year,
            period=start_date.month if frequency == TsFrequency.MONTHLY else 1,
            frequency=frequency
        )
        
        return cls(
            values=series.values,
            start_period=start_period,
            frequency=frequency,
            metadata={"name": series.name} if series.name else {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "values": self.values.tolist(),
            "start_period": {
                "year": self.start_period.year,
                "period": self.start_period.period,
                "frequency": self.start_period.frequency.value,
            },
            "frequency": self.frequency.value,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TsData":
        """Create from dictionary."""
        start_period = TsPeriod(
            year=data["start_period"]["year"],
            period=data["start_period"]["period"],
            frequency=TsFrequency(data["start_period"]["frequency"])
        )
        return cls(
            values=np.array(data["values"]),
            start_period=start_period,
            frequency=TsFrequency(data["frequency"]),
            metadata=data.get("metadata", {})
        )