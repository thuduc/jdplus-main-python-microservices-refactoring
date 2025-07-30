"""Time series plotter."""

from typing import List, Optional, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

from jdemetra_common.models import TsData
from ..schemas.requests import PlotStyle
from .base import BasePlotter


class TimeSeriesPlotter(BasePlotter):
    """Plotter for time series data."""
    
    def plot(self, 
             series: List[TsData], 
             output_path: str,
             format: str = "png",
             date_format: str = "%Y-%m",
             show_markers: bool = False,
             annotations: Optional[List[Dict[str, Any]]] = None) -> str:
        """Plot time series."""
        fig, ax = self._create_figure()
        
        # Get colors
        colors = self.style.colors or plt.cm.tab10.colors
        
        # Plot each series
        for i, ts in enumerate(series):
            dates = self._generate_dates(ts)
            color = colors[i % len(colors)]
            label = ts.metadata.get('name', f'Series {i+1}')
            
            # Plot line
            line_style = self.style.line_style or '-'
            ax.plot(dates, ts.values, 
                   line_style, 
                   color=color, 
                   label=label,
                   linewidth=2)
            
            # Add markers if requested
            if show_markers:
                marker_style = self.style.marker_style or 'o'
                ax.plot(dates, ts.values, 
                       marker_style, 
                       color=color,
                       markersize=4,
                       markeredgecolor='white',
                       markeredgewidth=0.5)
        
        # Add annotations
        if annotations:
            for ann in annotations:
                if 'date' in ann and 'text' in ann:
                    ax.annotate(
                        ann['text'],
                        xy=(pd.to_datetime(ann['date']), ann.get('y', 0)),
                        xytext=(10, 10),
                        textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                    )
        
        # Format dates
        self._format_dates(ax, date_format)
        
        # Apply styling
        self._apply_common_styling(ax)
        
        # Save plot
        return self.save_plot(fig, output_path, format)
    
    def _generate_dates(self, ts: TsData) -> pd.DatetimeIndex:
        """Generate dates for time series."""
        # Map frequency to pandas frequency
        freq_map = {
            'DAILY': 'D',
            'WEEKLY': 'W',
            'MONTHLY': 'M',
            'QUARTERLY': 'Q',
            'YEARLY': 'Y'
        }
        
        pd_freq = freq_map.get(ts.frequency.name, 'M')
        
        # Create start date
        if ts.frequency.name == 'MONTHLY':
            start_date = pd.Timestamp(year=ts.start_period.year, 
                                    month=ts.start_period.period, 
                                    day=1)
        elif ts.frequency.name == 'QUARTERLY':
            month = (ts.start_period.period - 1) * 3 + 1
            start_date = pd.Timestamp(year=ts.start_period.year, 
                                    month=month, 
                                    day=1)
        elif ts.frequency.name == 'YEARLY':
            start_date = pd.Timestamp(year=ts.start_period.year, 
                                    month=1, 
                                    day=1)
        else:
            # Default to monthly
            start_date = pd.Timestamp(year=ts.start_period.year, 
                                    month=1, 
                                    day=1)
        
        # Generate date range
        return pd.date_range(start=start_date, 
                           periods=len(ts.values), 
                           freq=pd_freq)