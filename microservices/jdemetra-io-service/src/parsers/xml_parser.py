"""XML parser implementation."""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from datetime import datetime

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from .base import BaseParser


class XMLParser(BaseParser):
    """Parser for XML files."""
    
    def parse(self, content: str) -> List[TsData]:
        """Parse XML content.
        
        Supports two formats:
        1. JDemetra+ XML format
        2. Generic time series XML format
        """
        root = ET.fromstring(content)
        
        # Check format
        if root.tag == 'jdemetra' or self.options.get('format') == 'jdemetra':
            return self._parse_jdemetra_format(root)
        else:
            return self._parse_generic_format(root)
    
    def _parse_jdemetra_format(self, root: ET.Element) -> List[TsData]:
        """Parse JDemetra+ XML format."""
        series_list = []
        
        for series_elem in root.findall('.//series'):
            # Extract metadata
            name = series_elem.get('name', 'unnamed')
            freq_str = series_elem.get('frequency', 'M')
            
            # Map frequency
            freq_map = {
                'D': TsFrequency.DAILY,
                'W': TsFrequency.WEEKLY,
                'M': TsFrequency.MONTHLY,
                'Q': TsFrequency.QUARTERLY,
                'Y': TsFrequency.YEARLY
            }
            frequency = freq_map.get(freq_str, TsFrequency.MONTHLY)
            
            # Extract start period
            start_elem = series_elem.find('start')
            if start_elem is not None:
                year = int(start_elem.get('year'))
                period = int(start_elem.get('period', '1'))
            else:
                # Try to parse from first observation
                first_obs = series_elem.find('.//observation')
                if first_obs is not None:
                    date_str = first_obs.get('date')
                    date = datetime.fromisoformat(date_str)
                    year = date.year
                    period = self._get_period_from_date(date, frequency)
                else:
                    year = 2020
                    period = 1
            
            start_period = TsPeriod(year, period, frequency)
            
            # Extract values
            values = []
            for obs_elem in series_elem.findall('.//observation'):
                value = float(obs_elem.get('value'))
                values.append(value)
            
            # Create time series
            metadata = {
                'name': name,
                'source': 'xml',
                'format': 'jdemetra'
            }
            
            # Add any additional attributes as metadata
            for key, value in series_elem.attrib.items():
                if key not in ['name', 'frequency']:
                    metadata[key] = value
            
            ts = TsData(
                values=values,
                start_period=start_period,
                frequency=frequency,
                metadata=metadata
            )
            series_list.append(ts)
        
        return series_list
    
    def _parse_generic_format(self, root: ET.Element) -> List[TsData]:
        """Parse generic XML format."""
        series_list = []
        
        # Try to find time series elements
        series_tags = self.options.get('series_tag', 'timeseries')
        if isinstance(series_tags, str):
            series_tags = [series_tags]
        
        for tag in series_tags:
            for series_elem in root.findall(f'.//{tag}'):
                ts = self._parse_generic_series(series_elem)
                if ts:
                    series_list.append(ts)
        
        # If no series found, try to parse root as series
        if not series_list:
            ts = self._parse_generic_series(root)
            if ts:
                series_list.append(ts)
        
        return series_list
    
    def _parse_generic_series(self, elem: ET.Element) -> TsData:
        """Parse a generic series element."""
        # Extract name
        name = elem.get('name') or elem.get('id') or elem.tag
        
        # Extract frequency
        freq_str = elem.get('frequency') or self.options.get('frequency', 'M')
        frequency = TsFrequency[freq_str] if hasattr(TsFrequency, freq_str) else TsFrequency.MONTHLY
        
        # Find observations
        obs_tag = self.options.get('observation_tag', 'observation')
        date_attr = self.options.get('date_attribute', 'date')
        value_attr = self.options.get('value_attribute', 'value')
        
        observations = elem.findall(f'.//{obs_tag}')
        if not observations:
            # Try alternative patterns
            observations = elem.findall('.//obs') or elem.findall('.//data')
        
        if not observations:
            return None
        
        # Extract values and dates
        values = []
        dates = []
        
        for obs in observations:
            # Get value
            value_str = obs.get(value_attr)
            if value_str is None:
                value_str = obs.text
            if value_str:
                try:
                    values.append(float(value_str.strip()))
                except ValueError:
                    continue
            
            # Get date if available
            date_str = obs.get(date_attr)
            if date_str:
                try:
                    dates.append(datetime.fromisoformat(date_str))
                except:
                    pass
        
        if not values:
            return None
        
        # Determine start period
        if dates:
            start_date = dates[0]
            year = start_date.year
            period = self._get_period_from_date(start_date, frequency)
        else:
            # Use defaults
            year = int(self.options.get('start_year', 2020))
            period = int(self.options.get('start_period', 1))
        
        start_period = TsPeriod(year, period, frequency)
        
        # Create time series
        ts = TsData(
            values=values,
            start_period=start_period,
            frequency=frequency,
            metadata={'name': name, 'source': 'xml'}
        )
        
        return ts
    
    def validate(self, content: str) -> tuple[bool, List[str]]:
        """Validate XML content."""
        errors = []
        
        try:
            root = ET.fromstring(content)
            
            # Check if it's a valid time series XML
            valid_roots = ['jdemetra', 'timeseries', 'series', 'data']
            if root.tag not in valid_roots and not self.options.get('series_tag'):
                errors.append(f"Unknown root element: {root.tag}")
            
            # Try to find at least one series
            series_found = False
            for tag in ['series', 'timeseries', self.options.get('series_tag')]:
                if tag and root.findall(f'.//{tag}'):
                    series_found = True
                    break
            
            if not series_found and not root.findall('.//observation'):
                errors.append("No time series data found in XML")
            
        except ET.ParseError as e:
            errors.append(f"Invalid XML: {str(e)}")
        except Exception as e:
            errors.append(f"Error parsing XML: {str(e)}")
        
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