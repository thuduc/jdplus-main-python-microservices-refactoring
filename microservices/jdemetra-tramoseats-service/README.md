# TRAMO/SEATS Service

TRAMO/SEATS seasonal adjustment service for JDemetra+.

## Features

- TRAMO model estimation (Time series Regression with ARIMA noise, Missing observations and Outliers)
- SEATS decomposition (Signal Extraction in ARIMA Time Series)
- Automatic model selection
- Outlier detection and correction
- Calendar effects estimation
- Specification management
- Asynchronous processing for large jobs

## API Endpoints

- `POST /api/v1/tramoseats/process` - Process time series with TRAMO/SEATS
- `POST /api/v1/tramoseats/specification` - Create/update specification
- `GET /api/v1/tramoseats/results/{id}` - Get processing results
- `POST /api/v1/tramoseats/diagnostics` - Run diagnostics on results

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Start Redis (for Celery):
```bash
redis-server
```

3. Start Celery worker:
```bash
celery -A src.worker worker --loglevel=info
```

4. Start the service:
```bash
uvicorn src.main:app --reload --port 8004
```