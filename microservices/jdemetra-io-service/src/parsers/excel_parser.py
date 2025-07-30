"""Excel parser implementation."""

import pandas as pd
from typing import List, Dict, Any
from io import BytesIO

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from .base import BaseParser


class ExcelParser(BaseParser):
    """Parser for Excel files."""
    
    def parse(self, content: str) -> List[TsData]:
        """Parse Excel content.
        
        Note: For Excel, content should be base64 encoded bytes.
        """
        import base64
        
        # Decode base64 content
        try:
            excel_bytes = base64.b64decode(content)
        except:
            # If not base64, assume it's already bytes
            excel_bytes = content.encode('latin-1')
        
        # Read Excel file
        df = pd.read_excel(
            BytesIO(excel_bytes),
            sheet_name=self.options.get('sheet', 0),
            header=0 if self.options.get('header', True) else None
        )
        
        # Extract date column
        date_col = self.options.get('date_column', 0)
        if isinstance(date_col, int):
            dates = df.iloc[:, date_col]
        else:
            dates = df[date_col]
        
        # Parse dates
        dates = pd.to_datetime(dates)
        
        # Determine frequency
        freq_str = self.options.get('frequency')
        if freq_str:
            frequency = TsFrequency[freq_str]
        else:
            # Auto-detect frequency
            freq = pd.infer_freq(dates)
            frequency = self._map_pandas_freq(freq)
        
        # Extract value columns
        value_cols = self.options.get('value_columns', [])
        if not value_cols:
            # Use all numeric columns except date column
            value_cols = [i for i in range(len(df.columns)) 
                         if i != date_col and pd.api.types.is_numeric_dtype(df.iloc[:, i])]
        
        # Create time series
        series_list = []
        
        for col in value_cols:
            if isinstance(col, int):
                values = df.iloc[:, col].values
                col_name = df.columns[col] if self.options.get('header', True) else f'column_{col}'
            else:
                values = df[col].values
                col_name = col
            
            # Create start period
            start_date = dates.iloc[0]
            start_period = TsPeriod(
                year=start_date.year,
                period=self._get_period_number(start_date, frequency),
                frequency=frequency
            )
            
            # Create time series
            ts = TsData(
                values=values.tolist(),
                start_period=start_period,
                frequency=frequency,
                metadata={'name': str(col_name), 'source': 'excel'}
            )
            series_list.append(ts)
        
        return series_list
    
    def validate(self, content: str) -> tuple[bool, List[str]]:
        """Validate Excel content."""
        errors = []
        
        try:
            import base64
            
            # Try to decode base64
            try:
                excel_bytes = base64.b64decode(content)
            except:
                excel_bytes = content.encode('latin-1')
            
            # Try to read Excel
            df = pd.read_excel(BytesIO(excel_bytes), nrows=5)
            
            if df.empty:
                errors.append("Excel file is empty")
            
            if len(df.columns) < 2:
                errors.append("Excel file must have at least 2 columns (date and values)")
            
        except Exception as e:
            errors.append(f"Invalid Excel file: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _map_pandas_freq(self, freq: str) -> TsFrequency:
        """Map pandas frequency to TsFrequency."""
        if not freq:
            return TsFrequency.UNDEFINED
        
        freq_map = {
            'D': TsFrequency.DAILY,
            'B': TsFrequency.DAILY,
            'W': TsFrequency.WEEKLY,
            'M': TsFrequency.MONTHLY,
            'MS': TsFrequency.MONTHLY,
            'Q': TsFrequency.QUARTERLY,
            'QS': TsFrequency.QUARTERLY,
            'A': TsFrequency.YEARLY,
            'AS': TsFrequency.YEARLY,
            'Y': TsFrequency.YEARLY,
            'YS': TsFrequency.YEARLY
        }
        
        # Get base frequency
        base_freq = freq.split('-')[0] if '-' in freq else freq
        return freq_map.get(base_freq, TsFrequency.UNDEFINED)
    
    def _get_period_number(self, date: pd.Timestamp, frequency: TsFrequency) -> int:
        """Get period number for a date based on frequency."""
        if frequency == TsFrequency.MONTHLY:
            return date.month
        elif frequency == TsFrequency.QUARTERLY:
            return (date.month - 1) // 3 + 1
        elif frequency == TsFrequency.WEEKLY:
            return date.isocalendar()[1]
        elif frequency == TsFrequency.DAILY:
            return date.dayofyear
        else:
            return 1