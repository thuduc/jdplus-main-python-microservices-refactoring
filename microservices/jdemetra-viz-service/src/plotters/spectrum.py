"""Spectrum plotter."""

from typing import List, Optional
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

from ..schemas.requests import PlotStyle
from .base import BasePlotter


class SpectrumPlotter(BasePlotter):
    """Plotter for spectral analysis."""
    
    def plot(self,
             frequencies: List[float],
             spectrum: List[float],
             output_path: str,
             format: str = "png",
             log_scale: bool = True,
             highlight_peaks: bool = True,
             peak_threshold: Optional[float] = None) -> str:
        """Plot spectrum."""
        fig, ax = self._create_figure()
        
        frequencies = np.array(frequencies)
        spectrum = np.array(spectrum)
        
        # Plot spectrum
        if log_scale:
            ax.semilogy(frequencies, spectrum, 'b-', linewidth=2)
        else:
            ax.plot(frequencies, spectrum, 'b-', linewidth=2)
        
        # Highlight peaks if requested
        if highlight_peaks:
            # Find peaks
            if peak_threshold is None:
                peak_threshold = np.mean(spectrum) + 2 * np.std(spectrum)
            
            peaks, properties = find_peaks(spectrum, height=peak_threshold)
            
            if len(peaks) > 0:
                # Plot peaks
                ax.plot(frequencies[peaks], spectrum[peaks], 'ro', 
                       markersize=8, label='Peaks')
                
                # Annotate major peaks (top 5)
                peak_heights = spectrum[peaks]
                top_peaks_idx = np.argsort(peak_heights)[-5:]
                
                for idx in top_peaks_idx:
                    peak_idx = peaks[idx]
                    freq = frequencies[peak_idx]
                    height = spectrum[peak_idx]
                    
                    # Convert frequency to period
                    if freq > 0:
                        period = 1 / freq
                        ax.annotate(f'{period:.1f}',
                                  xy=(freq, height),
                                  xytext=(5, 5),
                                  textcoords='offset points',
                                  fontsize=9,
                                  bbox=dict(boxstyle='round,pad=0.3', 
                                          fc='yellow', alpha=0.7))
        
        # Add reference lines for common frequencies
        # Monthly = 12 per year
        ax.axvline(x=1/12, color='green', linestyle='--', alpha=0.3, 
                  label='Annual cycle')
        # Quarterly = 4 per year  
        ax.axvline(x=1/4, color='orange', linestyle='--', alpha=0.3,
                  label='Quarterly cycle')
        
        # Styling
        ax.set_xlabel('Frequency', fontsize=12)
        ax.set_ylabel('Spectral Density', fontsize=12)
        ax.set_title('Spectral Analysis', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        # Set x-axis limits
        ax.set_xlim(0, 0.5)  # Nyquist frequency
        
        # Save plot
        return self.save_plot(fig, output_path, format)