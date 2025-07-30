# Data I/O Service

Data import/export service for JDemetra+.

## Features

- Multi-format support (CSV, Excel, JSON, XML, YAML)
- Batch import/export
- Format conversion
- Data validation
- MinIO object storage integration
- Streaming for large files

## Supported Formats

- **CSV**: Standard comma-separated values
- **Excel**: .xlsx and .xls files
- **JSON**: Time series in JSON format
- **XML**: SDMX and custom XML formats
- **YAML**: Configuration and data files

## API Endpoints

- `POST /api/v1/io/import/{format}` - Import data in specified format
- `POST /api/v1/io/export/{format}` - Export data to specified format
- `POST /api/v1/io/convert` - Convert between formats
- `GET /api/v1/io/formats` - List supported formats
- `POST /api/v1/io/validate` - Validate data file
- `GET /api/v1/io/download/{file_id}` - Download exported file

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Start MinIO (for file storage):
```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

3. Start the service:
```bash
uvicorn src.main:app --reload --port 8006
```