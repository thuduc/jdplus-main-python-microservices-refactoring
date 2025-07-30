"""Diagnostic plots."""

from typing import List, Optional
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

from ..schemas.requests import PlotStyle
from .base import BasePlotter


class DiagnosticsPlotter(BasePlotter):
    """Plotter for diagnostic plots."""
    
    def plot(self,
             residuals: List[float],
             plot_types: List[str],
             output_path: str,
             format: str = "png",
             max_lags: int = 40,
             confidence_level: float = 0.95) -> str:
        """Generate diagnostic plots."""
        n_plots = len(plot_types)
        
        # Determine layout
        if n_plots <= 2:
            nrows, ncols = 1, n_plots
        elif n_plots <= 4:
            nrows, ncols = 2, 2
        else:
            nrows = (n_plots + 1) // 2
            ncols = 2
        
        fig, axes = self._create_figure(nrows=nrows, ncols=ncols)
        if n_plots == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        # Generate each plot type
        plot_idx = 0
        for plot_type in plot_types:
            if plot_type == 'acf':
                self._plot_acf(residuals, axes[plot_idx], max_lags, confidence_level)
            elif plot_type == 'pacf':
                self._plot_pacf(residuals, axes[plot_idx], max_lags, confidence_level)
            elif plot_type == 'qq':
                self._plot_qq(residuals, axes[plot_idx])
            elif plot_type == 'histogram':
                self._plot_histogram(residuals, axes[plot_idx])
            elif plot_type == 'residuals':
                self._plot_residuals(residuals, axes[plot_idx])
            
            plot_idx += 1
        
        # Hide unused subplots
        for i in range(plot_idx, len(axes)):
            axes[i].set_visible(False)
        
        # Overall title
        fig.suptitle('Residual Diagnostics', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save plot
        return self.save_plot(fig, output_path, format)
    
    def _plot_acf(self, residuals: List[float], ax: plt.Axes, 
                  max_lags: int, confidence_level: float):
        """Plot autocorrelation function."""
        plot_acf(residuals, ax=ax, lags=max_lags, alpha=1-confidence_level)
        ax.set_title('Autocorrelation Function', fontsize=12)
        ax.set_xlabel('Lag')
        ax.set_ylabel('ACF')
    
    def _plot_pacf(self, residuals: List[float], ax: plt.Axes,
                   max_lags: int, confidence_level: float):
        """Plot partial autocorrelation function."""
        try:
            plot_pacf(residuals, ax=ax, lags=max_lags, alpha=1-confidence_level)
            ax.set_title('Partial Autocorrelation Function', fontsize=12)
            ax.set_xlabel('Lag')
            ax.set_ylabel('PACF')
        except:
            # Handle cases where PACF can't be computed
            ax.text(0.5, 0.5, 'PACF computation failed', 
                   transform=ax.transAxes, ha='center', va='center')
            ax.set_title('Partial Autocorrelation Function', fontsize=12)
    
    def _plot_qq(self, residuals: List[float], ax: plt.Axes):
        """Plot Q-Q plot."""
        stats.probplot(residuals, dist="norm", plot=ax)
        ax.set_title('Q-Q Plot', fontsize=12)
        ax.set_xlabel('Theoretical Quantiles')
        ax.set_ylabel('Sample Quantiles')
        ax.grid(True, alpha=0.3)
    
    def _plot_histogram(self, residuals: List[float], ax: plt.Axes):
        """Plot histogram with normal overlay."""
        n, bins, patches = ax.hist(residuals, bins=30, density=True, 
                                  alpha=0.7, color='blue', edgecolor='black')
        
        # Fit normal distribution
        mu, sigma = np.mean(residuals), np.std(residuals)
        x = np.linspace(min(residuals), max(residuals), 100)
        ax.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', lw=2, 
               label=f'Normal(μ={mu:.2f}, σ={sigma:.2f})')
        
        ax.set_title('Residual Distribution', fontsize=12)
        ax.set_xlabel('Residual Value')
        ax.set_ylabel('Density')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_residuals(self, residuals: List[float], ax: plt.Axes):
        """Plot residuals over time."""
        ax.plot(residuals, 'b-', linewidth=1)
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        # Add confidence bands
        std = np.std(residuals)
        ax.axhline(y=2*std, color='r', linestyle=':', alpha=0.3)
        ax.axhline(y=-2*std, color='r', linestyle=':', alpha=0.3)
        
        ax.set_title('Residual Plot', fontsize=12)
        ax.set_xlabel('Observation')
        ax.set_ylabel('Residual')
        ax.grid(True, alpha=0.3)