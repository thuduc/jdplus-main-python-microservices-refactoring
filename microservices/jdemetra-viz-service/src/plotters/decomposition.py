"""Decomposition plotter."""

from typing import Optional
import matplotlib.pyplot as plt
import pandas as pd

from jdemetra_common.models import TsData
from ..schemas.requests import PlotStyle
from .base import BasePlotter


class DecompositionPlotter(BasePlotter):
    """Plotter for seasonal adjustment decomposition."""
    
    def plot(self,
             original: TsData,
             trend: TsData,
             seasonal: TsData,
             irregular: TsData,
             output_path: str,
             format: str = "png",
             method_name: str = "Decomposition") -> str:
        """Plot decomposition components."""
        # Create 4-panel plot
        fig, axes = self._create_figure(nrows=4, ncols=1)
        fig.suptitle(f'{method_name} Results', fontsize=16, fontweight='bold')
        
        # Generate dates
        dates = self._generate_dates(original)
        
        # Plot each component
        components = [
            (original, 'Original', axes[0], 'black'),
            (trend, 'Trend', axes[1], 'blue'),
            (seasonal, 'Seasonal', axes[2], 'green'),
            (irregular, 'Irregular', axes[3], 'red')
        ]
        
        for ts, label, ax, color in components:
            ax.plot(dates, ts.values, color=color, linewidth=1.5)
            ax.set_ylabel(label, fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            if ax != axes[-1]:
                ax.set_xticklabels([])
            else:
                self._format_dates(ax)
        
        # Adjust layout
        plt.tight_layout()
        
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