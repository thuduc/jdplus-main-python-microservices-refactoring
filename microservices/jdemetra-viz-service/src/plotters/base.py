"""Base plotter class."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

from ..schemas.requests import PlotStyle
from ..core.config import settings


class BasePlotter(ABC):
    """Base class for all plotters."""
    
    def __init__(self, style: Optional[PlotStyle] = None):
        self.style = style or PlotStyle()
        self._setup_style()
    
    def _setup_style(self):
        """Setup matplotlib style."""
        theme = self.style.theme or settings.DEFAULT_THEME
        if theme in plt.style.available:
            plt.style.use(theme)
        
        # Set figure size
        self.figure_size = self.style.figure_size or list(settings.DEFAULT_FIGURE_SIZE)
        self.dpi = self.style.dpi or settings.DEFAULT_DPI
    
    def _create_figure(self, nrows: int = 1, ncols: int = 1) -> Tuple[plt.Figure, Any]:
        """Create figure with subplots."""
        fig, ax = plt.subplots(
            nrows, ncols,
            figsize=self.figure_size,
            dpi=self.dpi,
            tight_layout=True
        )
        return fig, ax
    
    def _apply_common_styling(self, ax: plt.Axes):
        """Apply common styling to axes."""
        if self.style.title:
            ax.set_title(self.style.title, fontsize=14, fontweight='bold')
        
        if self.style.xlabel:
            ax.set_xlabel(self.style.xlabel, fontsize=12)
        
        if self.style.ylabel:
            ax.set_ylabel(self.style.ylabel, fontsize=12)
        
        if self.style.grid is not None:
            ax.grid(self.style.grid, alpha=0.3)
        
        if self.style.legend is not None and self.style.legend:
            ax.legend(loc='best')
    
    def _format_dates(self, ax: plt.Axes, date_format: str = "%Y-%m"):
        """Format date axis."""
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def save_plot(self, fig: plt.Figure, output_path: str, format: str = "png"):
        """Save plot to file."""
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save with appropriate settings
        save_kwargs = {
            'bbox_inches': 'tight',
            'pad_inches': 0.1
        }
        
        if format == 'png':
            save_kwargs['dpi'] = self.dpi
        elif format == 'svg':
            save_kwargs['format'] = 'svg'
        elif format == 'pdf':
            save_kwargs['format'] = 'pdf'
        
        fig.savefig(output_path, **save_kwargs)
        
        # Clean up
        plt.close(fig)
        
        return output_path
    
    @abstractmethod
    def plot(self, *args, **kwargs) -> str:
        """Generate plot and return file path."""
        pass