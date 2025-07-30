# X-13ARIMA-SEATS Service

X-13ARIMA-SEATS seasonal adjustment service for JDemetra+.

## Features

- X-13ARIMA-SEATS processing
- RegARIMA modeling
- X-11 decomposition
- SEATS decomposition option
- Automatic model selection
- Outlier detection
- Calendar and holiday effects
- Specification management
- Asynchronous processing

## API Endpoints

- `POST /api/v1/x13/process` - Process time series with X-13
- `POST /api/v1/x13/specification` - Create/update specification
- `GET /api/v1/x13/results/{id}` - Get processing results
- `POST /api/v1/x13/diagnostics` - Run diagnostics
- `POST /api/v1/x13/compare` - Compare multiple specifications

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
uvicorn src.main:app --reload --port 8005
```