"""Excel formatter implementation."""

import pandas as pd
import base64
from typing import List, Dict, Any
from io import BytesIO

from jdemetra_common.models import TsData
from .base import BaseFormatter


class ExcelFormatter(BaseFormatter):
    """Formatter for Excel files."""
    
    def format(self, series: List[TsData]) -> str:
        """Format time series as Excel.
        
        Returns base64 encoded Excel file content.
        """
        # Determine layout
        layout = self.options.get('layout', 'wide')
        
        if layout == 'wide':
            df = self._format_wide(series)
        else:
            df = self._format_long(series)
        
        # Write to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            sheet_name = self.options.get('sheet_name', 'TimeSeries')
            df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False if self.options.get('header', True) else True
            )
            
            # Add metadata sheet if requested
            if self.options.get('include_metadata', False):
                metadata_df = self._create_metadata_df(series)
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        # Return base64 encoded content
        excel_bytes = output.getvalue()
        return base64.b64encode(excel_bytes).decode('utf-8')
    
    def _format_wide(self, series: List[TsData]) -> pd.DataFrame:
        """Format as wide table (one column per series)."""
        if not series:
            return pd.DataFrame()
        
        # Create date index from first series
        first_series = series[0]
        dates = self._generate_dates(first_series)
        
        # Create dataframe
        data = {'Date': dates}
        
        for ts in series:
            name = ts.metadata.get('name', f'series_{len(data)}')
            # Ensure same length
            if len(ts.values) == len(dates):
                data[name] = ts.values
            else:
                # Pad or truncate
                values = list(ts.values)
                if len(values) < len(dates):
                    values.extend([None] * (len(dates) - len(values)))
                else:
                    values = values[:len(dates)]
                data[name] = values
        
        df = pd.DataFrame(data)
        
        # Format dates
        date_format = self.options.get('date_format', '%Y-%m-%d')
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime(date_format)
        
        return df
    
    def _format_long(self, series: List[TsData]) -> pd.DataFrame:
        """Format as long table (stacked format)."""
        if not series:
            return pd.DataFrame()
        
        rows = []
        
        for ts in series:
            name = ts.metadata.get('name', 'unnamed')
            dates = self._generate_dates(ts)
            
            for i, (date, value) in enumerate(zip(dates, ts.values)):
                rows.append({
                    'Series': name,
                    'Date': date,
                    'Value': value
                })
        
        df = pd.DataFrame(rows)
        
        # Format dates
        date_format = self.options.get('date_format', '%Y-%m-%d')
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime(date_format)
        
        return df
    
    def _create_metadata_df(self, series: List[TsData]) -> pd.DataFrame:
        """Create metadata dataframe."""
        rows = []
        
        for ts in series:
            row = {
                'Name': ts.metadata.get('name', 'unnamed'),
                'Frequency': ts.frequency.name,
                'Start Year': ts.start_period.year,
                'Start Period': ts.start_period.period,
                'Length': len(ts.values)
            }
            
            # Add other metadata
            for key, value in ts.metadata.items():
                if key not in ['name']:
                    row[key.title()] = str(value)
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def _generate_dates(self, ts: TsData) -> List[pd.Timestamp]:
        """Generate date series for time series."""
        start_date = self._ts_period_to_date(ts.start_period)
        
        # Map frequency
        freq_map = {
            'DAILY': 'D',
            'WEEKLY': 'W',
            'MONTHLY': 'M',
            'QUARTERLY': 'Q',
            'YEARLY': 'Y'
        }
        
        pd_freq = freq_map.get(ts.frequency.name, 'M')
        
        return pd.date_range(
            start=start_date,
            periods=len(ts.values),
            freq=pd_freq
        )
    
    def _ts_period_to_date(self, period) -> pd.Timestamp:
        """Convert TsPeriod to pandas Timestamp."""
        if period.frequency.name == 'MONTHLY':
            return pd.Timestamp(year=period.year, month=period.period, day=1)
        elif period.frequency.name == 'QUARTERLY':
            month = (period.period - 1) * 3 + 1
            return pd.Timestamp(year=period.year, month=month, day=1)
        elif period.frequency.name == 'YEARLY':
            return pd.Timestamp(year=period.year, month=1, day=1)
        elif period.frequency.name == 'WEEKLY':
            # Approximate - week number to date
            return pd.Timestamp(year=period.year, month=1, day=1) + pd.Timedelta(weeks=period.period-1)
        elif period.frequency.name == 'DAILY':
            # Day of year
            return pd.Timestamp(year=period.year, month=1, day=1) + pd.Timedelta(days=period.period-1)
        else:
            return pd.Timestamp(year=period.year, month=1, day=1)