# Statistical Analysis Service

Statistical analysis and testing service for JDemetra+.

## Features

- Statistical tests (normality, stationarity, randomness)
- Distribution fitting and testing
- Descriptive statistics computation
- Hypothesis testing
- Time series specific statistics

## API Endpoints

- `POST /api/v1/stats/test/normality` - Test for normality
- `POST /api/v1/stats/test/stationarity` - Test for stationarity
- `POST /api/v1/stats/descriptive` - Compute descriptive statistics
- `POST /api/v1/stats/distribution/fit` - Fit distribution to data
- `POST /api/v1/stats/test/randomness` - Test for randomness
- `POST /api/v1/stats/test/seasonality` - Test for seasonality

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Start the service:
```bash
uvicorn src.main:app --reload --port 8002
```