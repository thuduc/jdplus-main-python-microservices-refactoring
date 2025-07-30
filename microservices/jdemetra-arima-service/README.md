# ARIMA Modeling Service

ARIMA model estimation and forecasting service for JDemetra+.

## Features

- ARIMA model estimation with automatic order selection
- Forecasting with confidence intervals
- Model diagnostics and validation
- Seasonal ARIMA (SARIMA) support
- Model persistence and caching

## API Endpoints

- `POST /api/v1/arima/estimate` - Estimate ARIMA model
- `POST /api/v1/arima/forecast` - Generate forecasts
- `POST /api/v1/arima/identify` - Automatic model identification
- `GET /api/v1/arima/model/{id}` - Retrieve saved model
- `POST /api/v1/arima/diagnose` - Model diagnostics

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Start the service:
```bash
uvicorn src.main:app --reload --port 8003
```