"""YAML parser implementation."""

import yaml
from typing import List, Dict, Any
from datetime import datetime

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from .base import BaseParser


class YAMLParser(BaseParser):
    """Parser for YAML files."""
    
    def parse(self, content: str) -> List[TsData]:
        """Parse YAML content."""
        data = yaml.safe_load(content)
        
        # Handle different YAML structures
        if isinstance(data, list):
            # List of series
            return self._parse_series_list(data)
        elif isinstance(data, dict):
            if 'series' in data or 'timeseries' in data:
                # Structured format with series key
                series_data = data.get('series', data.get('timeseries', []))
                if isinstance(series_data, list):
                    return self._parse_series_list(series_data)
                else:
                    return [self._parse_single_series(series_data)]
            else:
                # Single series as dict
                return [self._parse_single_series(data)]
        else:
            raise ValueError("Invalid YAML structure for time series data")
    
    def _parse_series_list(self, series_list: List[Dict]) -> List[TsData]:
        """Parse a list of series."""
        result = []
        for series_data in series_list:
            ts = self._parse_single_series(series_data)
            if ts:
                result.append(ts)
        return result
    
    def _parse_single_series(self, data: Dict) -> TsData:
        """Parse a single series from dict."""
        # Extract values
        values_key = self.options.get('values_key', 'values')
        if values_key not in data:
            # Try alternative keys
            for key in ['data', 'observations', 'obs']:
                if key in data:
                    values_key = key
                    break
        
        values = data.get(values_key, [])
        if not values:
            return None
        
        # Ensure values are floats
        values = [float(v) for v in values]
        
        # Extract metadata
        name = data.get('name', data.get('id', 'unnamed'))
        
        # Extract frequency
        freq_str = data.get('frequency', self.options.get('frequency', 'M'))
        if hasattr(TsFrequency, freq_str):
            frequency = TsFrequency[freq_str]
        else:
            # Try to map common frequency strings
            freq_map = {
                'monthly': TsFrequency.MONTHLY,
                'quarterly': TsFrequency.QUARTERLY,
                'yearly': TsFrequency.YEARLY,
                'annual': TsFrequency.YEARLY,
                'daily': TsFrequency.DAILY,
                'weekly': TsFrequency.WEEKLY
            }
            frequency = freq_map.get(freq_str.lower(), TsFrequency.MONTHLY)
        
        # Extract start period
        if 'start_period' in data:
            sp = data['start_period']
            if isinstance(sp, dict):
                year = sp.get('year', 2020)
                period = sp.get('period', 1)
            else:
                # Assume it's a year
                year = int(sp)
                period = 1
        elif 'start' in data:
            # Try to parse as date
            start = data['start']
            if isinstance(start, str):
                try:
                    start_date = datetime.fromisoformat(start)
                    year = start_date.year
                    period = self._get_period_from_date(start_date, frequency)
                except:
                    year = int(start) if start.isdigit() else 2020
                    period = 1
            else:
                year = int(start)
                period = 1
        else:
            year = self.options.get('start_year', 2020)
            period = self.options.get('start_period', 1)
        
        start_period = TsPeriod(year, period, frequency)
        
        # Build metadata
        metadata = {'name': str(name), 'source': 'yaml'}
        
        # Add any extra fields as metadata
        exclude_keys = {values_key, 'name', 'id', 'frequency', 'start_period', 'start'}
        for key, value in data.items():
            if key not in exclude_keys and not key.startswith('_'):
                metadata[key] = value
        
        # Create time series
        ts = TsData(
            values=values,
            start_period=start_period,
            frequency=frequency,
            metadata=metadata
        )
        
        return ts
    
    def validate(self, content: str) -> tuple[bool, List[str]]:
        """Validate YAML content."""
        errors = []
        
        try:
            data = yaml.safe_load(content)
            
            if data is None:
                errors.append("Empty YAML file")
                return False, errors
            
            # Check structure
            if isinstance(data, list):
                if not data:
                    errors.append("Empty series list")
                else:
                    # Validate first series
                    first = data[0]
                    if not isinstance(first, dict):
                        errors.append("Series must be dictionaries")
                    elif 'values' not in first and 'data' not in first:
                        errors.append("Series must contain 'values' or 'data' field")
            elif isinstance(data, dict):
                if 'series' in data or 'timeseries' in data:
                    # Nested structure
                    series = data.get('series', data.get('timeseries'))
                    if not series:
                        errors.append("Empty series list")
                elif 'values' not in data and 'data' not in data:
                    errors.append("Series must contain 'values' or 'data' field")
            else:
                errors.append(f"Invalid YAML structure: expected dict or list, got {type(data).__name__}")
            
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML: {str(e)}")
        except Exception as e:
            errors.append(f"Error parsing YAML: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _get_period_from_date(self, date: datetime, frequency: TsFrequency) -> int:
        """Get period number from date."""
        if frequency == TsFrequency.MONTHLY:
            return date.month
        elif frequency == TsFrequency.QUARTERLY:
            return (date.month - 1) // 3 + 1
        elif frequency == TsFrequency.WEEKLY:
            return date.isocalendar()[1]
        elif frequency == TsFrequency.DAILY:
            return date.timetuple().tm_yday
        else:
            return 1