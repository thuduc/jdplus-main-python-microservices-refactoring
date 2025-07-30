"""JSON formatter implementation."""

import json
from typing import List, Dict, Any

from jdemetra_common.models import TsData


class JSONFormatter:
    """Format time series to JSON."""
    
    def __init__(self, options: Dict[str, Any]):
        self.format_type = options.get("format_type", "jdemetra")
        self.indent = options.get("indent", 2)
        self.include_metadata = options.get("include_metadata", True)
    
    def format(self, series_list: List[TsData]) -> str:
        """Format time series to JSON."""
        if self.format_type == "jdemetra":
            return self._format_jdemetra(series_list)
        elif self.format_type == "simple":
            return self._format_simple(series_list)
        else:
            raise ValueError(f"Unknown JSON format type: {self.format_type}")
    
    def _format_jdemetra(self, series_list: List[TsData]) -> str:
        """Format as JDemetra+ JSON."""
        if len(series_list) == 1:
            # Single series
            data = series_list[0].to_dict()
        else:
            # Multiple series
            data = {
                "series": [ts.to_dict() for ts in series_list]
            }
        
        return json.dumps(data, indent=self.indent)
    
    def _format_simple(self, series_list: List[TsData]) -> str:
        """Format as simple JSON."""
        data = {}
        
        for ts in series_list:
            name = ts.metadata.get("name", f"series_{len(data)}")
            
            # Generate dates
            dates = ts._generate_date_index()
            
            if ts.frequency == TsFrequency.MONTHLY:
                date_strings = [d.strftime("%Y-%m") for d in dates]
            elif ts.frequency == TsFrequency.QUARTERLY:
                date_strings = [f"{d.year}Q{(d.month-1)//3+1}" for d in dates]
            else:
                date_strings = [str(d.year) for d in dates]
            
            series_data = {
                "dates": date_strings,
                "values": ts.values.tolist()
            }
            
            if self.include_metadata:
                series_data["metadata"] = ts.metadata
            
            data[name] = series_data
        
        return json.dumps(data, indent=self.indent)