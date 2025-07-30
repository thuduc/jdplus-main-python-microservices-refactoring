"""I/O API endpoints."""

import io
import time
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from ..schemas.requests import ImportRequest, ExportRequest, ConvertRequest, ValidateRequest
from ..schemas.responses import (
    ImportResponse, ExportResponse, ConvertResponse, 
    ValidationResult, FormatsResponse, FormatInfo, ImportedSeries
)
from ..parsers.csv_parser import CSVParser
from ..parsers.json_parser import JSONParser
from ..parsers.excel_parser import ExcelParser
from ..parsers.xml_parser import XMLParser
from ..parsers.yaml_parser import YAMLParser
from ..formatters.csv_formatter import CSVFormatter
from ..formatters.json_formatter import JSONFormatter
from ..formatters.excel_formatter import ExcelFormatter
from ..formatters.xml_formatter import XMLFormatter
from ..formatters.yaml_formatter import YAMLFormatter
from ..core.config import settings
from ..main import get_minio

router = APIRouter()


# Format registry
FORMATS = {
    "csv": {
        "name": "Comma-Separated Values",
        "extensions": [".csv"],
        "parser": CSVParser,
        "formatter": CSVFormatter,
        "options": {
            "import": {
                "delimiter": "Delimiter character (default: ,)",
                "header": "Has header row (default: true)",
                "date_column": "Date column index or name",
                "value_columns": "Value column indices or names",
                "frequency": "Time series frequency",
                "date_format": "Date format string"
            },
            "export": {
                "delimiter": "Delimiter character (default: ,)",
                "header": "Include header row (default: true)",
                "date_format": "Date format string",
                "layout": "wide or long format"
            }
        }
    },
    "json": {
        "name": "JavaScript Object Notation",
        "extensions": [".json"],
        "parser": JSONParser,
        "formatter": JSONFormatter,
        "options": {
            "import": {
                "format_type": "jdemetra or simple"
            },
            "export": {
                "format_type": "jdemetra or simple",
                "indent": "Indentation level",
                "include_metadata": "Include metadata"
            }
        }
    },
    "excel": {
        "name": "Microsoft Excel",
        "extensions": [".xlsx", ".xls"],
        "parser": ExcelParser,
        "formatter": ExcelFormatter,
        "options": {
            "import": {
                "sheet": "Sheet name or index (default: 0)",
                "header": "Has header row (default: true)",
                "date_column": "Date column index or name",
                "value_columns": "Value column indices or names",
                "frequency": "Time series frequency"
            },
            "export": {
                "layout": "wide or long format",
                "sheet_name": "Sheet name (default: TimeSeries)",
                "date_format": "Date format string",
                "include_metadata": "Include metadata sheet"
            }
        }
    },
    "xml": {
        "name": "Extensible Markup Language",
        "extensions": [".xml"],
        "parser": XMLParser,
        "formatter": XMLFormatter,
        "options": {
            "import": {
                "format": "jdemetra or generic",
                "series_tag": "XML tag for series elements",
                "observation_tag": "XML tag for observations",
                "date_attribute": "Attribute name for dates",
                "value_attribute": "Attribute name for values"
            },
            "export": {
                "format_type": "jdemetra or generic",
                "pretty_print": "Format with indentation",
                "include_metadata": "Include metadata elements",
                "include_dates": "Include dates with observations"
            }
        }
    },
    "yaml": {
        "name": "YAML Ain't Markup Language",
        "extensions": [".yaml", ".yml"],
        "parser": YAMLParser,
        "formatter": YAMLFormatter,
        "options": {
            "import": {
                "values_key": "Key name for values array",
                "frequency": "Default frequency if not specified"
            },
            "export": {
                "format_type": "structured or simple",
                "indent": "Indentation level",
                "include_metadata": "Include metadata fields",
                "include_dates": "Include dates with values"
            }
        }
    }
}


@router.post("/io/upload")
async def upload_file(file: UploadFile = File(...), minio_client=Depends(get_minio)):
    """Upload a file for processing."""
    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Validate extension
    file_ext = "." + file.filename.split(".")[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {file_ext}")
    
    # Upload to MinIO
    file_id = f"{uuid4()}_{file.filename}"
    minio_client.put_object(
        settings.MINIO_BUCKET,
        file_id,
        io.BytesIO(content),
        len(content)
    )
    
    return {"file_id": file_id, "size": len(content)}


@router.post("/io/import/{format}", response_model=ImportResponse)
async def import_data(format: str, request: ImportRequest, minio_client=Depends(get_minio)):
    """Import data from uploaded file."""
    if format not in FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    
    start_time = time.time()
    
    try:
        # Download file from MinIO
        response = minio_client.get_object(settings.MINIO_BUCKET, request.file_id)
        content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        
        # Parse content
        parser_class = FORMATS[format]["parser"]
        parser = parser_class(request.options)
        series_list = parser.parse(content)
        
        # Create response
        imported_series = []
        for ts in series_list:
            series_id = uuid4()
            imported_series.append(ImportedSeries(
                series_id=series_id,
                name=ts.metadata.get("name"),
                metadata=ts.metadata
            ))
        
        return ImportResponse(
            import_id=uuid4(),
            status="completed",
            imported_series=imported_series,
            total_series=len(imported_series),
            warnings=[],
            import_time=time.time() - start_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


@router.post("/io/export/{format}", response_model=ExportResponse)
async def export_data(format: str, request: ExportRequest, minio_client=Depends(get_minio)):
    """Export data to specified format."""
    if format not in FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    
    try:
        # For demo, create mock time series
        from jdemetra_common.models import TsData, TsPeriod, TsFrequency
        import numpy as np
        
        series_list = []
        for i, series_id in enumerate(request.series_ids):
            ts = TsData(
                values=np.random.normal(100, 10, 50),
                start_period=TsPeriod(2020, 1, TsFrequency.MONTHLY),
                frequency=TsFrequency.MONTHLY,
                metadata={"name": f"series_{i}", "id": str(series_id)}
            )
            series_list.append(ts)
        
        # Format data
        formatter_class = FORMATS[format]["formatter"]
        formatter = formatter_class(request.options)
        formatted_content = formatter.format(series_list)
        
        # Upload to MinIO
        filename = request.filename or f"export_{uuid4()}.{format}"
        file_id = f"exports/{filename}"
        
        minio_client.put_object(
            settings.MINIO_BUCKET,
            file_id,
            io.BytesIO(formatted_content.encode()),
            len(formatted_content)
        )
        
        # Generate download URL
        download_url = f"/api/v1/io/download/{file_id}"
        
        return ExportResponse(
            export_id=uuid4(),
            file_id=file_id,
            download_url=download_url,
            format=format,
            file_size=len(formatted_content),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Export failed: {str(e)}")


@router.post("/io/convert", response_model=ConvertResponse)
async def convert_format(request: ConvertRequest, minio_client=Depends(get_minio)):
    """Convert between formats."""
    if request.source_format not in FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported source format: {request.source_format}")
    if request.target_format not in FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported target format: {request.target_format}")
    
    start_time = time.time()
    
    try:
        # Download source file
        response = minio_client.get_object(settings.MINIO_BUCKET, request.source_file_id)
        content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        
        # Parse with source format
        parser_class = FORMATS[request.source_format]["parser"]
        parser = parser_class(request.options.get("parse_options", {}))
        series_list = parser.parse(content)
        
        # Format with target format
        formatter_class = FORMATS[request.target_format]["formatter"]
        formatter = formatter_class(request.options.get("format_options", {}))
        formatted_content = formatter.format(series_list)
        
        # Upload converted file
        target_file_id = f"converted/{uuid4()}.{request.target_format}"
        minio_client.put_object(
            settings.MINIO_BUCKET,
            target_file_id,
            io.BytesIO(formatted_content.encode()),
            len(formatted_content)
        )
        
        download_url = f"/api/v1/io/download/{target_file_id}"
        
        return ConvertResponse(
            conversion_id=uuid4(),
            source_file=request.source_file_id,
            target_file=target_file_id,
            download_url=download_url,
            conversion_time=time.time() - start_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")


@router.get("/io/formats", response_model=FormatsResponse)
async def list_formats():
    """List supported formats."""
    format_list = []
    
    for fmt_id, fmt_info in FORMATS.items():
        format_list.append(FormatInfo(
            format=fmt_id,
            name=fmt_info["name"],
            extensions=fmt_info["extensions"],
            supports_import="parser" in fmt_info,
            supports_export="formatter" in fmt_info,
            options=fmt_info["options"]
        ))
    
    return FormatsResponse(formats=format_list)


@router.post("/io/validate", response_model=ValidationResult)
async def validate_file(request: ValidateRequest, minio_client=Depends(get_minio)):
    """Validate file format."""
    try:
        # Download file
        response = minio_client.get_object(settings.MINIO_BUCKET, request.file_id)
        content = response.read().decode('utf-8')
        file_size = len(content)
        response.close()
        response.release_conn()
        
        # Validate with appropriate parser
        if request.format in FORMATS and "parser" in FORMATS[request.format]:
            parser_class = FORMATS[request.format]["parser"]
            parser = parser_class({})
            valid, errors = parser.validate(content)
            
            # Try to detect actual format
            format_detected = request.format if valid else None
            
            return ValidationResult(
                valid=valid,
                format_detected=format_detected,
                errors=errors,
                warnings=[],
                file_info={
                    "size": file_size,
                    "lines": content.count('\n') + 1
                }
            )
        else:
            raise HTTPException(status_code=400, detail=f"Format {request.format} does not support validation")
            
    except Exception as e:
        return ValidationResult(
            valid=False,
            format_detected=None,
            errors=[str(e)],
            warnings=[],
            file_info={}
        )


@router.get("/io/download/{file_id:path}")
async def download_file(file_id: str, minio_client=Depends(get_minio)):
    """Download exported file."""
    try:
        # Get file from MinIO
        response = minio_client.get_object(settings.MINIO_BUCKET, file_id)
        content = response.read()
        response.close()
        response.release_conn()
        
        # Determine content type
        if file_id.endswith('.csv'):
            media_type = "text/csv"
        elif file_id.endswith('.json'):
            media_type = "application/json"
        elif file_id.endswith('.xml'):
            media_type = "application/xml"
        elif file_id.endswith('.yaml') or file_id.endswith('.yml'):
            media_type = "application/x-yaml"
        else:
            media_type = "application/octet-stream"
        
        filename = file_id.split('/')[-1]
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")