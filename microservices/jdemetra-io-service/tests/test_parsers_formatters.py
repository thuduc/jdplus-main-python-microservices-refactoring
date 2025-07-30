"""Tests for all parsers and formatters."""

import pytest
import base64
import xml.etree.ElementTree as ET
import yaml
import json
from jdemetra_common.models import TsData, TsPeriod, TsFrequency

from src.parsers.csv_parser import CSVParser
from src.parsers.json_parser import JSONParser
from src.parsers.excel_parser import ExcelParser
from src.parsers.xml_parser import XMLParser
from src.parsers.yaml_parser import YAMLParser

from src.formatters.csv_formatter import CSVFormatter
from src.formatters.json_formatter import JSONFormatter
from src.formatters.excel_formatter import ExcelFormatter
from src.formatters.xml_formatter import XMLFormatter
from src.formatters.yaml_formatter import YAMLFormatter


class TestCSVParserFormatter:
    """Test CSV parser and formatter."""
    
    def test_csv_round_trip(self):
        """Test parsing and formatting CSV."""
        # Create test data
        ts1 = TsData(
            values=[100.0, 101.0, 102.0, 103.0],
            start_period=TsPeriod(2020, 1, TsFrequency.MONTHLY),
            frequency=TsFrequency.MONTHLY,
            metadata={"name": "series1"}
        )
        ts2 = TsData(
            values=[200.0, 201.0, 202.0, 203.0],
            start_period=TsPeriod(2020, 1, TsFrequency.MONTHLY),
            frequency=TsFrequency.MONTHLY,
            metadata={"name": "series2"}
        )
        
        # Format to CSV
        formatter = CSVFormatter({})
        csv_content = formatter.format([ts1, ts2])
        
        # Parse back
        parser = CSVParser({"header": True})
        parsed = parser.parse(csv_content)
        
        assert len(parsed) == 2
        assert parsed[0].values == pytest.approx(ts1.values)
        assert parsed[1].values == pytest.approx(ts2.values)


class TestJSONParserFormatter:
    """Test JSON parser and formatter."""
    
    def test_json_jdemetra_format(self):
        """Test JDemetra JSON format."""
        ts = TsData(
            values=[100.0, 101.0, 102.0],
            start_period=TsPeriod(2020, 1, TsFrequency.QUARTERLY),
            frequency=TsFrequency.QUARTERLY,
            metadata={"name": "quarterly_series"}
        )
        
        # Format
        formatter = JSONFormatter({"format_type": "jdemetra"})
        json_content = formatter.format([ts])
        
        # Parse
        parser = JSONParser({"format_type": "jdemetra"})
        parsed = parser.parse(json_content)
        
        assert len(parsed) == 1
        assert parsed[0].values == pytest.approx(ts.values)
        assert parsed[0].frequency == TsFrequency.QUARTERLY
        assert parsed[0].start_period.year == 2020
        assert parsed[0].start_period.period == 1


class TestExcelParserFormatter:
    """Test Excel parser and formatter."""
    
    def test_excel_wide_format(self):
        """Test Excel wide format."""
        ts1 = TsData(
            values=[100.0, 101.0, 102.0],
            start_period=TsPeriod(2020, 1, TsFrequency.MONTHLY),
            frequency=TsFrequency.MONTHLY,
            metadata={"name": "series1"}
        )
        
        # Format to Excel (base64)
        formatter = ExcelFormatter({"layout": "wide"})
        excel_b64 = formatter.format([ts1])
        
        # Verify it's base64
        assert base64.b64decode(excel_b64)  # Should not raise
        
    def test_excel_long_format(self):
        """Test Excel long format."""
        ts1 = TsData(
            values=[100.0, 101.0],
            start_period=TsPeriod(2020, 1, TsFrequency.YEARLY),
            frequency=TsFrequency.YEARLY,
            metadata={"name": "annual_data"}
        )
        
        formatter = ExcelFormatter({"layout": "long"})
        excel_b64 = formatter.format([ts1])
        
        # Verify it's valid base64
        assert base64.b64decode(excel_b64)


class TestXMLParserFormatter:
    """Test XML parser and formatter."""
    
    def test_xml_jdemetra_format(self):
        """Test JDemetra XML format."""
        ts = TsData(
            values=[1.0, 2.0, 3.0, 4.0],
            start_period=TsPeriod(2020, 1, TsFrequency.QUARTERLY),
            frequency=TsFrequency.QUARTERLY,
            metadata={"name": "test_series", "source": "test"}
        )
        
        # Format
        formatter = XMLFormatter({"format_type": "jdemetra", "pretty_print": False})
        xml_content = formatter.format([ts])
        
        # Parse
        parser = XMLParser({"format": "jdemetra"})
        parsed = parser.parse(xml_content)
        
        assert len(parsed) == 1
        assert parsed[0].values == pytest.approx(ts.values)
        assert parsed[0].metadata["name"] == "test_series"
    
    def test_xml_generic_format(self):
        """Test generic XML format."""
        # Create generic XML
        xml_content = """
        <data>
            <timeseries name="test" frequency="M">
                <observation date="2020-01-01" value="100"/>
                <observation date="2020-02-01" value="101"/>
                <observation date="2020-03-01" value="102"/>
            </timeseries>
        </data>
        """
        
        parser = XMLParser({})
        parsed = parser.parse(xml_content.strip())
        
        assert len(parsed) == 1
        assert len(parsed[0].values) == 3
        assert parsed[0].values == pytest.approx([100.0, 101.0, 102.0])


class TestYAMLParserFormatter:
    """Test YAML parser and formatter."""
    
    def test_yaml_simple_format(self):
        """Test simple YAML format."""
        ts = TsData(
            values=[10.0, 20.0, 30.0],
            start_period=TsPeriod(2021, 1, TsFrequency.MONTHLY),
            frequency=TsFrequency.MONTHLY,
            metadata={"name": "monthly_data"}
        )
        
        # Format
        formatter = YAMLFormatter({"format_type": "simple"})
        yaml_content = formatter.format([ts])
        
        # Parse
        parser = YAMLParser({})
        parsed = parser.parse(yaml_content)
        
        assert len(parsed) == 1
        assert parsed[0].values == pytest.approx(ts.values)
        assert parsed[0].start_period.year == 2021
    
    def test_yaml_structured_format(self):
        """Test structured YAML format."""
        ts1 = TsData(
            values=[1.0, 2.0],
            start_period=TsPeriod(2022, 1, TsFrequency.YEARLY),
            frequency=TsFrequency.YEARLY,
            metadata={"name": "annual", "unit": "millions"}
        )
        
        formatter = YAMLFormatter({"format_type": "structured", "include_dates": True})
        yaml_content = formatter.format([ts1])
        
        # Verify structure
        data = yaml.safe_load(yaml_content)
        assert "timeseries_data" in data
        assert "series" in data
        assert len(data["series"]) == 1
        assert data["series"][0]["id"] == "annual"
    
    def test_yaml_parsing_flexibility(self):
        """Test YAML parser with different structures."""
        # Test list format
        yaml_list = """
        - name: series1
          frequency: MONTHLY
          start_year: 2020
          start_period: 1
          values: [100, 101, 102]
        - name: series2
          frequency: MONTHLY  
          start_year: 2020
          start_period: 1
          values: [200, 201, 202]
        """
        
        parser = YAMLParser({})
        parsed = parser.parse(yaml_list)
        assert len(parsed) == 2
        assert parsed[0].metadata["name"] == "series1"
        assert parsed[1].metadata["name"] == "series2"


class TestValidation:
    """Test validation methods."""
    
    def test_csv_validation(self):
        """Test CSV validation."""
        parser = CSVParser({})
        
        # Valid CSV
        valid_csv = "Date,Value1,Value2\n2020-01-01,100,200\n2020-02-01,101,201"
        valid, errors = parser.validate(valid_csv)
        assert valid
        assert len(errors) == 0
        
        # Invalid CSV (empty)
        valid, errors = parser.validate("")
        assert not valid
        assert len(errors) > 0
    
    def test_json_validation(self):
        """Test JSON validation."""
        parser = JSONParser({})
        
        # Valid JSON
        valid_json = '{"series": [{"name": "test", "values": [1,2,3]}]}'
        valid, errors = parser.validate(valid_json)
        assert valid
        
        # Invalid JSON
        invalid_json = '{"series": [{"name": "test", "values": [1,2,3'
        valid, errors = parser.validate(invalid_json)
        assert not valid
    
    def test_xml_validation(self):
        """Test XML validation."""
        parser = XMLParser({})
        
        # Valid XML
        valid_xml = '<series><observation value="100"/></series>'
        valid, errors = parser.validate(valid_xml)
        assert valid
        
        # Invalid XML
        invalid_xml = '<series><observation value="100"'
        valid, errors = parser.validate(invalid_xml)
        assert not valid
    
    def test_yaml_validation(self):
        """Test YAML validation."""
        parser = YAMLParser({})
        
        # Valid YAML
        valid_yaml = "name: test\nvalues: [1, 2, 3]"
        valid, errors = parser.validate(valid_yaml)
        assert valid
        
        # Invalid YAML structure
        invalid_yaml = "- name: test"  # List with no values
        valid, errors = parser.validate(invalid_yaml)
        assert not valid