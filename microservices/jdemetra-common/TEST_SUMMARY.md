# Test Summary for jdemetra-common

## Overview
The jdemetra-common library provides shared data models and schemas used across all JDemetra+ microservices.

## Test Coverage

### Model Tests (`tests/test_models.py`)
- ✅ **TsPeriod Tests**
  - Test creation with different frequencies
  - Test string representation
  - Test equality comparison
  - Test dictionary conversion

- ✅ **TsData Tests**
  - Test creation with values and period
  - Test length calculation
  - Test metadata handling
  - Test dictionary conversion

- ✅ **ArimaModel Tests**
  - Test model creation with orders
  - Test coefficient storage
  - Test AIC/BIC/likelihood values
  - Test residuals handling

- ✅ **SeasonalComponent Tests**
  - Test component creation
  - Test filter weights
  - Test component values

### Schema Tests (`tests/test_schemas.py`)
- ✅ **TimeSeriesSchema Tests**
  - Test serialization/deserialization
  - Test validation of required fields
  - Test frequency validation
  - Test metadata handling

- ✅ **ArimaModelSchema Tests**
  - Test model schema validation
  - Test optional fields handling
  - Test nested residual schema

- ✅ **RequestSchema Tests**
  - Test request validation
  - Test optional parameters
  - Test default values

## Test Statistics
- **Total Test Files**: 2
- **Total Test Cases**: 15+
- **Coverage Areas**:
  - Data models (TsPeriod, TsData, ArimaModel, etc.)
  - Pydantic schemas for API contracts
  - Serialization/deserialization
  - Validation logic

## Key Test Scenarios

### Time Series Data Handling
```python
def test_ts_data_creation():
    ts = TsData(
        values=[1.0, 2.0, 3.0],
        start_period=TsPeriod(2020, 1, TsFrequency.MONTHLY),
        frequency=TsFrequency.MONTHLY
    )
    assert len(ts) == 3
    assert ts.values == [1.0, 2.0, 3.0]
```

### ARIMA Model Representation
```python
def test_arima_model():
    model = ArimaModel(
        order=(1, 1, 1),
        seasonal_order=(0, 1, 1, 12),
        coefficients={'ar.1': 0.5, 'ma.1': -0.3}
    )
    assert model.order == (1, 1, 1)
    assert model.seasonal_order == (0, 1, 1, 12)
```

### Schema Validation
```python
def test_timeseries_schema_validation():
    schema = TimeSeriesSchema(
        values=[1, 2, 3],
        start_period=StartPeriodSchema(year=2020, period=1, frequency="M"),
        frequency="M"
    )
    assert schema.frequency == "M"
```

## Dependencies Tested
- Pydantic models and validation
- NumPy array handling
- Enum-based frequency types
- Optional field handling
- Metadata dictionaries

## Notes
- All models are designed to be immutable where appropriate
- Schemas provide strict validation for API contracts
- Models support conversion to/from dictionaries for serialization
- Comprehensive equality checking implemented for data comparison