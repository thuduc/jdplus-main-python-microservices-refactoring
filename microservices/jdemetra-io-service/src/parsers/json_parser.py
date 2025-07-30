"""JSON parser implementation."""

import json
from typing import List, Dict, Any
import numpy as np

from jdemetra_common.models import TsData, TsPeriod, TsFrequency


class JSONParser:
    """Parse JSON files to time series."""
    
    def __init__(self, options: Dict[str, Any]):
        self.format_type = options.get("format_type", "jdemetra")
    
    def parse(self, content: str) -> List[TsData]:
        """Parse JSON content to time series."""
        data = json.loads(content)
        
        if self.format_type == "jdemetra":
            return self._parse_jdemetra_format(data)
        elif self.format_type == "simple":
            return self._parse_simple_format(data)
        else:
            raise ValueError(f"Unknown JSON format type: {self.format_type}")
    
    def _parse_jdemetra_format(self, data: Dict[str, Any]) -> List[TsData]:
        """Parse JDemetra+ JSON format."""
        series_list = []
        
        if "series" in data:
            # Multiple series
            for series_data in data["series"]:
                ts = TsData.from_dict(series_data)
                series_list.append(ts)
        else:
            # Single series
            ts = TsData.from_dict(data)
            series_list.append(ts)
        
        return series_list
    
    def _parse_simple_format(self, data: Dict[str, Any]) -> List[TsData]:
        """Parse simple JSON format."""
        series_list = []
        
        # Expected format: {"series_name": {"dates": [...], "values": [...]}, ...}
        for name, series_data in data.items():
            if not isinstance(series_data, dict):
                continue
            
            values = series_data.get("values", [])
            if not values:
                continue
            
            # Detect frequency from dates if provided
            dates = series_data.get("dates", [])
            if dates and len(dates) >= 2:
                # Simple frequency detection
                if "Q" in dates[0]:
                    freq = TsFrequency.QUARTERLY
                elif "-" in dates[0] and len(dates[0].split("-")) == 2:
                    freq = TsFrequency.MONTHLY
                else:
                    freq = TsFrequency.YEARLY
                
                # Parse start period
                if freq == TsFrequency.MONTHLY:
                    year, month = map(int, dates[0].split("-"))
                    start_period = TsPeriod(year, month, freq)
                elif freq == TsFrequency.QUARTERLY:
                    year = int(dates[0][:4])
                    quarter = int(dates[0][-1])
                    start_period = TsPeriod(year, quarter, freq)
                else:
                    year = int(dates[0])
                    start_period = TsPeriod(year, 1, freq)
            else:
                # Default to monthly
                freq = TsFrequency.MONTHLY
                start_period = TsPeriod(2020, 1, freq)
            
            ts = TsData(
                values=np.array(values),
                start_period=start_period,
                frequency=freq,
                metadata={"name": name, "source": "json"}
            )
            
            series_list.append(ts)
        
        return series_list
    
    def validate(self, content: str) -> tuple[bool, List[str]]:
        """Validate JSON content."""
        errors = []
        
        try:
            data = json.loads(content)
            
            if not isinstance(data, dict):
                errors.append("JSON must be an object")
            
            if self.format_type == "jdemetra":
                # Validate JDemetra format
                if "series" in data:
                    if not isinstance(data["series"], list):
                        errors.append("'series' must be an array")
                else:
                    # Single series - check required fields
                    if "values" not in data:
                        errors.append("Missing 'values' field")
                    if "start_period" not in data:
                        errors.append("Missing 'start_period' field")
                    if "frequency" not in data:
                        errors.append("Missing 'frequency' field")
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            errors.append(f"JSON validation failed: {str(e)}")
        
        return len(errors) == 0, errors