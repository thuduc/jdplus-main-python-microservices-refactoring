"""XML formatter implementation."""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Any
from datetime import datetime

from jdemetra_common.models import TsData
from .base import BaseFormatter


class XMLFormatter(BaseFormatter):
    """Formatter for XML files."""
    
    def format(self, series: List[TsData]) -> str:
        """Format time series as XML."""
        format_type = self.options.get('format_type', 'jdemetra')
        
        if format_type == 'jdemetra':
            root = self._format_jdemetra(series)
        else:
            root = self._format_generic(series)
        
        # Convert to string
        if self.options.get('pretty_print', True):
            return self._prettify(root)
        else:
            return ET.tostring(root, encoding='unicode')
    
    def _format_jdemetra(self, series: List[TsData]) -> ET.Element:
        """Format as JDemetra+ XML."""
        root = ET.Element('jdemetra')
        root.set('version', '2.0')
        
        # Add metadata
        metadata = ET.SubElement(root, 'metadata')
        ET.SubElement(metadata, 'created').text = datetime.utcnow().isoformat()
        ET.SubElement(metadata, 'source').text = 'jdemetra-io-service'
        
        # Add series
        series_container = ET.SubElement(root, 'series_collection')
        
        for ts in series:
            series_elem = ET.SubElement(series_container, 'series')
            
            # Add attributes
            series_elem.set('name', ts.metadata.get('name', 'unnamed'))
            series_elem.set('frequency', self._frequency_to_code(ts.frequency))
            
            # Add start period
            start_elem = ET.SubElement(series_elem, 'start')
            start_elem.set('year', str(ts.start_period.year))
            start_elem.set('period', str(ts.start_period.period))
            
            # Add metadata
            if self.options.get('include_metadata', True):
                meta_elem = ET.SubElement(series_elem, 'metadata')
                for key, value in ts.metadata.items():
                    if key != 'name':
                        item = ET.SubElement(meta_elem, 'item')
                        item.set('key', key)
                        item.text = str(value)
            
            # Add observations
            obs_container = ET.SubElement(series_elem, 'observations')
            obs_container.set('count', str(len(ts.values)))
            
            dates = self._generate_dates(ts)
            for i, (date, value) in enumerate(zip(dates, ts.values)):
                obs = ET.SubElement(obs_container, 'observation')
                obs.set('index', str(i))
                obs.set('date', date.isoformat())
                obs.set('value', str(value))
        
        return root
    
    def _format_generic(self, series: List[TsData]) -> ET.Element:
        """Format as generic XML."""
        root_tag = self.options.get('root_tag', 'timeseries_data')
        root = ET.Element(root_tag)
        
        series_tag = self.options.get('series_tag', 'timeseries')
        obs_tag = self.options.get('observation_tag', 'observation')
        
        for ts in series:
            series_elem = ET.SubElement(root, series_tag)
            
            # Add series attributes
            series_elem.set('id', ts.metadata.get('name', 'unnamed'))
            if self.options.get('include_frequency', True):
                series_elem.set('frequency', ts.frequency.name)
            
            # Add header info
            if self.options.get('include_header', True):
                header = ET.SubElement(series_elem, 'header')
                ET.SubElement(header, 'name').text = ts.metadata.get('name', 'unnamed')
                ET.SubElement(header, 'start_year').text = str(ts.start_period.year)
                ET.SubElement(header, 'start_period').text = str(ts.start_period.period)
                ET.SubElement(header, 'length').text = str(len(ts.values))
            
            # Add data
            data_elem = ET.SubElement(series_elem, 'data')
            
            if self.options.get('include_dates', True):
                dates = self._generate_dates(ts)
                for date, value in zip(dates, ts.values):
                    obs = ET.SubElement(data_elem, obs_tag)
                    obs.set('date', date.strftime('%Y-%m-%d'))
                    obs.set('value', str(value))
            else:
                for i, value in enumerate(ts.values):
                    obs = ET.SubElement(data_elem, obs_tag)
                    obs.set('index', str(i))
                    obs.set('value', str(value))
        
        return root
    
    def _prettify(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string."""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent='  ', encoding=None)
    
    def _frequency_to_code(self, frequency) -> str:
        """Convert TsFrequency to single letter code."""
        freq_map = {
            'DAILY': 'D',
            'WEEKLY': 'W',
            'MONTHLY': 'M',
            'QUARTERLY': 'Q',
            'YEARLY': 'Y'
        }
        return freq_map.get(frequency.name, 'U')
    
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
                # Day of year
                date = datetime(year, 1, 1)
                date = date.replace(year=year, month=1, day=1)
                from datetime import timedelta
                date = date + timedelta(days=period-1+i)
            else:
                # Default to monthly
                date = datetime(year, 1, 1)
            
            dates.append(date)
        
        return dates