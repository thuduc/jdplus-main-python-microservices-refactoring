"""YAML formatter implementation."""

import yaml
from typing import List, Dict, Any
from datetime import datetime

from jdemetra_common.models import TsData
from .base import BaseFormatter


class YAMLFormatter(BaseFormatter):
    """Formatter for YAML files."""
    
    def format(self, series: List[TsData]) -> str:
        """Format time series as YAML."""
        format_type = self.options.get('format_type', 'structured')
        
        if format_type == 'simple':
            data = self._format_simple(series)
        else:
            data = self._format_structured(series)
        
        # Convert to YAML
        return yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            indent=self.options.get('indent', 2),
            allow_unicode=True
        )
    
    def _format_simple(self, series: List[TsData]) -> List[Dict[str, Any]]:
        """Format as simple list of series."""
        result = []
        
        for ts in series:
            series_dict = {
                'name': ts.metadata.get('name', 'unnamed'),
                'frequency': ts.frequency.name,
                'start_year': ts.start_period.year,
                'start_period': ts.start_period.period,
                'values': ts.values
            }
            
            # Add metadata if requested
            if self.options.get('include_metadata', False):
                for key, value in ts.metadata.items():
                    if key not in ['name']:
                        series_dict[key] = value
            
            result.append(series_dict)
        
        return result
    
    def _format_structured(self, series: List[TsData]) -> Dict[str, Any]:
        """Format as structured document."""
        document = {
            'timeseries_data': {
                'version': '1.0',
                'created': datetime.utcnow().isoformat(),
                'source': 'jdemetra-io-service',
                'series_count': len(series)
            }
        }
        
        # Add series
        series_list = []
        
        for ts in series:
            series_data = {
                'id': ts.metadata.get('name', 'unnamed'),
                'metadata': {
                    'frequency': ts.frequency.name,
                    'start': {
                        'year': ts.start_period.year,
                        'period': ts.start_period.period
                    },
                    'length': len(ts.values)
                }
            }
            
            # Add custom metadata
            for key, value in ts.metadata.items():
                if key not in ['name']:
                    series_data['metadata'][key] = value
            
            # Add data based on options
            if self.options.get('include_dates', False):
                # Include dates with values
                dates = self._generate_dates(ts)
                observations = []
                for date, value in zip(dates, ts.values):
                    observations.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'value': float(value)
                    })
                series_data['observations'] = observations
            else:
                # Just values array
                series_data['values'] = [float(v) for v in ts.values]
            
            series_list.append(series_data)
        
        document['series'] = series_list
        
        return document
    
    def _generate_dates(self, ts: TsData) -> List[datetime]:
        """Generate dates for time series."""
        dates = []
        year = ts.start_period.year
        period = ts.start_period.period
        
        for i in range(len(ts.values)):
            if ts.frequency.name == 'MONTHLY':
                date = datetime(year, period, 1)
                period += 1
                if period > 12:
                    period = 1
                    year += 1
            elif ts.frequency.name == 'QUARTERLY':
                month = (period - 1) * 3 + 1
                date = datetime(year, month, 1)
                period += 1
                if period > 4:
                    period = 1
                    year += 1
            elif ts.frequency.name == 'YEARLY':
                date = datetime(year, 1, 1)
                year += 1
            elif ts.frequency.name == 'DAILY':
                # Day of year - simplified
                from datetime import timedelta
                date = datetime(year, 1, 1) + timedelta(days=period-1+i)
            elif ts.frequency.name == 'WEEKLY':
                # Week of year - simplified
                from datetime import timedelta
                date = datetime(year, 1, 1) + timedelta(weeks=period-1+i)
            else:
                # Default to start of year
                date = datetime(year, 1, 1)
            
            dates.append(date)
        
        return dates