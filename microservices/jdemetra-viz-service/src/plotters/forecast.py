"""Forecast plotter."""

from typing import Optional
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from jdemetra_common.models import TsData
from ..schemas.requests import PlotStyle
from .base import BasePlotter


class ForecastPlotter(BasePlotter):
    """Plotter for forecast visualization."""
    
    def plot(self,
             historical: TsData,
             forecast: TsData,
             output_path: str,
             format: str = "png",
             lower_bound: Optional[TsData] = None,
             upper_bound: Optional[TsData] = None,
             show_history_points: int = 50,
             confidence_level: float = 0.95) -> str:
        """Plot forecast with confidence intervals."""
        fig, ax = self._create_figure()
        
        # Generate dates
        hist_dates = self._generate_dates(historical)
        forecast_dates = self._generate_dates(forecast)
        
        # Determine how much history to show
        if show_history_points < len(historical.values):
            hist_start_idx = len(historical.values) - show_history_points
            hist_dates = hist_dates[hist_start_idx:]
            hist_values = historical.values[hist_start_idx:]
        else:
            hist_values = historical.values
        
        # Plot historical data
        ax.plot(hist_dates, hist_values, 'b-', linewidth=2, 
               label='Historical')
        
        # Plot forecast
        ax.plot(forecast_dates, forecast.values, 'r--', linewidth=2,
               label='Forecast')
        
        # Connect historical and forecast
        if len(hist_dates) > 0 and len(forecast_dates) > 0:
            ax.plot([hist_dates[-1], forecast_dates[0]], 
                   [hist_values[-1], forecast.values[0]],
                   'r--', linewidth=2)
        
        # Plot confidence intervals if provided
        if lower_bound and upper_bound:
            ax.fill_between(forecast_dates,
                          lower_bound.values,
                          upper_bound.values,
                          alpha=0.2,
                          color='red',
                          label=f'{int(confidence_level*100)}% CI')
        
        # Add vertical line at forecast start
        if len(hist_dates) > 0:
            ax.axvline(x=hist_dates[-1], color='gray', 
                      linestyle=':', alpha=0.5)
        
        # Styling
        self._format_dates(ax)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title('Forecast', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        # Save plot
        return self.save_plot(fig, output_path, format)
    
    def _generate_dates(self, ts: TsData) -> pd.DatetimeIndex:
        """Generate dates for time series."""
        freq_map = {
            'DAILY': 'D',
            'WEEKLY': 'W',
            'MONTHLY': 'M',
            'QUARTERLY': 'Q',
            'YEARLY': 'Y'
        }
        
        pd_freq = freq_map.get(ts.frequency.name, 'M')
        
        if ts.frequency.name == 'MONTHLY':
            start_date = pd.Timestamp(year=ts.start_period.year, 
                                    month=ts.start_period.period, 
                                    day=1)
        elif ts.frequency.name == 'QUARTERLY':
            month = (ts.start_period.period - 1) * 3 + 1
            start_date = pd.Timestamp(year=ts.start_period.year, 
                                    month=month, 
                                    day=1)
        else:
            start_date = pd.Timestamp(year=ts.start_period.year, 
                                    month=1, 
                                    day=1)
        
        return pd.date_range(start=start_date, 
                           periods=len(ts.values), 
                           freq=pd_freq)