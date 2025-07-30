"""CSV formatter implementation."""

import pandas as pd
from typing import List, Dict, Any
from io import StringIO

from jdemetra_common.models import TsData


class CSVFormatter:
    """Format time series to CSV."""
    
    def __init__(self, options: Dict[str, Any]):
        self.delimiter = options.get("delimiter", ",")
        self.include_header = options.get("header", True)
        self.date_format = options.get("date_format", "%Y-%m")
        self.layout = options.get("layout", "wide")  # wide or long
    
    def format(self, series_list: List[TsData]) -> str:
        """Format time series to CSV."""
        if self.layout == "wide":
            return self._format_wide(series_list)
        else:
            return self._format_long(series_list)
    
    def _format_wide(self, series_list: List[TsData]) -> str:
        """Format as wide CSV (one column per series)."""
        # Convert all series to pandas
        dfs = []
        for ts in series_list:
            series = ts.to_pandas()
            series.name = ts.metadata.get("name", f"series_{len(dfs)}")
            dfs.append(series)
        
        # Combine into single dataframe
        if dfs:
            df = pd.concat(dfs, axis=1)
            
            # Format dates
            df.index = df.index.strftime(self.date_format)
            
            # Convert to CSV
            output = StringIO()
            df.to_csv(
                output,
                sep=self.delimiter,
                header=self.include_header,
                index=True
            )
            return output.getvalue()
        
        return ""
    
    def _format_long(self, series_list: List[TsData]) -> str:
        """Format as long CSV (stacked format)."""
        rows = []
        
        for ts in series_list:
            name = ts.metadata.get("name", "unnamed")
            dates = ts._generate_date_index()
            
            for i, (date, value) in enumerate(zip(dates, ts.values)):
                rows.append({
                    "date": date.strftime(self.date_format),
                    "series": name,
                    "value": value
                })
        
        if rows:
            df = pd.DataFrame(rows)
            
            # Convert to CSV
            output = StringIO()
            df.to_csv(
                output,
                sep=self.delimiter,
                header=self.include_header,
                index=False
            )
            return output.getvalue()
        
        return ""