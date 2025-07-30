# Time Series Data Service

Microservice for managing time series data in JDemetra+.

## Features

- Time series CRUD operations
- Data validation and transformation
- Metadata management
- Redis caching for performance
- PostgreSQL storage with TimescaleDB

## API Endpoints

- `POST /api/v1/timeseries/create` - Create new time series
- `GET /api/v1/timeseries/{id}` - Retrieve time series
- `PUT /api/v1/timeseries/{id}/transform` - Apply transformations
- `DELETE /api/v1/timeseries/{id}` - Delete time series
- `POST /api/v1/timeseries/validate` - Validate time series data

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Set environment variables:
```bash
export DATABASE_URL=postgresql://user:pass@localhost/tsdata
export REDIS_URL=redis://localhost:6379
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the service:
```bash
uvicorn src.main:app --reload
```