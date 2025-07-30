"""CSV parser implementation."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from io import StringIO

from jdemetra_common.models import TsData, TsPeriod, TsFrequency


class CSVParser:
    """Parse CSV files to time series."""
    
    def __init__(self, options: Dict[str, Any]):
        self.delimiter = options.get("delimiter", ",")
        self.has_header = options.get("header", True)
        self.date_column = options.get("date_column", 0)
        self.value_columns = options.get("value_columns", None)
        self.frequency = options.get("frequency", "M")
        self.date_format = options.get("date_format", None)
    
    def parse(self, content: str) -> List[TsData]:
        """Parse CSV content to time series."""
        # Read CSV
        df = pd.read_csv(
            StringIO(content),
            delimiter=self.delimiter,
            header=0 if self.has_header else None
        )
        
        # Parse dates
        if isinstance(self.date_column, int):
            date_col = df.columns[self.date_column]
        else:
            date_col = self.date_column
        
        df[date_col] = pd.to_datetime(df[date_col], format=self.date_format)
        df = df.set_index(date_col)
        df = df.sort_index()
        
        # Determine value columns
        if self.value_columns is None:
            # All numeric columns except date
            value_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            if isinstance(self.value_columns[0], int):
                value_cols = [df.columns[i] for i in self.value_columns]
            else:
                value_cols = self.value_columns
        
        # Convert to time series
        series_list = []
        for col in value_cols:
            values = df[col].dropna().values
            
            if len(values) == 0:
                continue
            
            # Create TsPeriod for start
            start_date = df[col].dropna().index[0]
            freq = TsFrequency(self.frequency)
            
            if freq == TsFrequency.MONTHLY:
                start_period = TsPeriod(start_date.year, start_date.month, freq)
            elif freq == TsFrequency.QUARTERLY:
                start_period = TsPeriod(start_date.year, (start_date.month - 1) // 3 + 1, freq)
            elif freq == TsFrequency.YEARLY:
                start_period = TsPeriod(start_date.year, 1, freq)
            else:
                start_period = TsPeriod(start_date.year, 1, freq)
            
            ts = TsData(
                values=values,
                start_period=start_period,
                frequency=freq,
                metadata={"name": col, "source": "csv"}
            )
            
            series_list.append(ts)
        
        return series_list
    
    def validate(self, content: str) -> tuple[bool, List[str]]:
        """Validate CSV content."""
        errors = []
        
        try:
            df = pd.read_csv(
                StringIO(content),
                delimiter=self.delimiter,
                header=0 if self.has_header else None
            )
            
            if df.empty:
                errors.append("CSV file is empty")
            
            if len(df.columns) < 2:
                errors.append("CSV must have at least 2 columns (date and values)")
            
            # Check date column
            try:
                date_col = df.columns[self.date_column] if isinstance(self.date_column, int) else self.date_column
                pd.to_datetime(df[date_col], format=self.date_format)
            except Exception as e:
                errors.append(f"Date column parsing failed: {str(e)}")
            
        except Exception as e:
            errors.append(f"CSV parsing failed: {str(e)}")
        
        return len(errors) == 0, errors