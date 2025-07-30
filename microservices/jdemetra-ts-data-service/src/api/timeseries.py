"""Time series API endpoints."""

from typing import Optional
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from ..db.connection import get_db, get_redis
from ..db.models import TimeSeries
from ..schemas.requests import CreateTimeSeriesRequest, TransformRequest, BatchCreateRequest
from ..schemas.responses import TimeSeriesResponse, TimeSeriesListResponse, ValidationResponse
from ..core.transformations import apply_transformation
from ..core.validation import validate_timeseries
from ..core.config import settings

router = APIRouter()


@router.post("/timeseries/create", response_model=TimeSeriesResponse)
async def create_timeseries(
    request: CreateTimeSeriesRequest,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Create a new time series."""
    # Validate series length
    if len(request.values) > settings.MAX_SERIES_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Series length exceeds maximum of {settings.MAX_SERIES_LENGTH}"
        )
    
    # Create TsData object for validation
    ts_data = TsData(
        values=request.values,
        start_period=TsPeriod(
            year=request.start_period.year,
            period=request.start_period.period,
            frequency=request.start_period.frequency
        ),
        frequency=request.frequency,
        metadata=request.metadata
    )
    
    # Validate
    is_valid, errors, _ = validate_timeseries(ts_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid time series: {', '.join(errors)}")
    
    # Create database record
    ts = TimeSeries(
        name=request.name,
        frequency=request.frequency.value,
        start_year=request.start_period.year,
        start_period=request.start_period.period,
        values=request.values,
        metadata=request.metadata
    )
    
    db.add(ts)
    await db.commit()
    await db.refresh(ts)
    
    # Cache the time series
    cache_key = f"ts:{ts.id}"
    await redis.setex(
        cache_key,
        settings.CACHE_TTL,
        json.dumps(ts_data.to_dict())
    )
    
    return TimeSeriesResponse(
        id=ts.id,
        name=ts.name,
        values=ts.values,
        start_period=request.start_period,
        frequency=request.frequency,
        metadata=ts.metadata,
        created_at=ts.created_at,
        updated_at=ts.updated_at
    )


@router.get("/timeseries/{id}", response_model=TimeSeriesResponse)
async def get_timeseries(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Get a time series by ID."""
    # Check cache first
    cache_key = f"ts:{id}"
    cached = await redis.get(cache_key)
    
    if cached:
        ts_data = TsData.from_dict(json.loads(cached))
        # Still need to get metadata from DB
        result = await db.execute(
            select(TimeSeries).where(TimeSeries.id == id)
        )
        ts = result.scalar_one_or_none()
        if not ts:
            raise HTTPException(status_code=404, detail="Time series not found")
            
        return TimeSeriesResponse(
            id=ts.id,
            name=ts.name,
            values=ts_data.values.tolist(),
            start_period={
                "year": ts_data.start_period.year,
                "period": ts_data.start_period.period,
                "frequency": ts_data.start_period.frequency
            },
            frequency=ts_data.frequency,
            metadata=ts_data.metadata,
            created_at=ts.created_at,
            updated_at=ts.updated_at
        )
    
    # Get from database
    result = await db.execute(
        select(TimeSeries).where(TimeSeries.id == id)
    )
    ts = result.scalar_one_or_none()
    
    if not ts:
        raise HTTPException(status_code=404, detail="Time series not found")
    
    # Cache for next time
    ts_data = TsData(
        values=ts.values,
        start_period=TsPeriod(
            year=ts.start_year,
            period=ts.start_period,
            frequency=TsFrequency(ts.frequency)
        ),
        frequency=TsFrequency(ts.frequency),
        metadata=ts.metadata
    )
    await redis.setex(cache_key, settings.CACHE_TTL, json.dumps(ts_data.to_dict()))
    
    return TimeSeriesResponse(
        id=ts.id,
        name=ts.name,
        values=ts.values,
        start_period={
            "year": ts.start_year,
            "period": ts.start_period,
            "frequency": ts.frequency
        },
        frequency=TsFrequency(ts.frequency),
        metadata=ts.metadata,
        created_at=ts.created_at,
        updated_at=ts.updated_at
    )


@router.put("/timeseries/{id}/transform", response_model=TimeSeriesResponse)
async def transform_timeseries(
    id: UUID,
    request: TransformRequest,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Apply transformation to a time series."""
    # Get the time series
    result = await db.execute(
        select(TimeSeries).where(TimeSeries.id == id)
    )
    ts = result.scalar_one_or_none()
    
    if not ts:
        raise HTTPException(status_code=404, detail="Time series not found")
    
    # Create TsData object
    ts_data = TsData(
        values=ts.values,
        start_period=TsPeriod(
            year=ts.start_year,
            period=ts.start_period,
            frequency=TsFrequency(ts.frequency)
        ),
        frequency=TsFrequency(ts.frequency),
        metadata=ts.metadata
    )
    
    # Apply transformation
    try:
        transformed = apply_transformation(ts_data, request.operation, request.parameters)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Update database
    ts.values = transformed.values.tolist()
    ts.start_year = transformed.start_period.year
    ts.start_period = transformed.start_period.period
    ts.metadata = transformed.metadata
    
    await db.commit()
    await db.refresh(ts)
    
    # Invalidate cache
    cache_key = f"ts:{id}"
    await redis.delete(cache_key)
    
    return TimeSeriesResponse(
        id=ts.id,
        name=ts.name,
        values=ts.values,
        start_period={
            "year": ts.start_year,
            "period": ts.start_period,
            "frequency": ts.frequency
        },
        frequency=TsFrequency(ts.frequency),
        metadata=ts.metadata,
        created_at=ts.created_at,
        updated_at=ts.updated_at
    )


@router.delete("/timeseries/{id}")
async def delete_timeseries(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Delete a time series."""
    result = await db.execute(
        select(TimeSeries).where(TimeSeries.id == id)
    )
    ts = result.scalar_one_or_none()
    
    if not ts:
        raise HTTPException(status_code=404, detail="Time series not found")
    
    await db.delete(ts)
    await db.commit()
    
    # Remove from cache
    cache_key = f"ts:{id}"
    await redis.delete(cache_key)
    
    return {"message": "Time series deleted successfully"}


@router.post("/timeseries/validate", response_model=ValidationResponse)
async def validate_timeseries_endpoint(request: CreateTimeSeriesRequest):
    """Validate time series data without saving."""
    ts_data = TsData(
        values=request.values,
        start_period=TsPeriod(
            year=request.start_period.year,
            period=request.start_period.period,
            frequency=request.start_period.frequency
        ),
        frequency=request.frequency,
        metadata=request.metadata
    )
    
    is_valid, errors, warnings = validate_timeseries(ts_data)
    
    return ValidationResponse(
        valid=is_valid,
        errors=errors,
        warnings=warnings
    )


@router.get("/timeseries", response_model=TimeSeriesListResponse)
async def list_timeseries(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    frequency: Optional[str] = None,
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List time series with pagination."""
    # Build query
    query = select(TimeSeries)
    count_query = select(func.count()).select_from(TimeSeries)
    
    if frequency:
        query = query.where(TimeSeries.frequency == frequency)
        count_query = count_query.where(TimeSeries.frequency == frequency)
    
    if name:
        query = query.where(TimeSeries.name.ilike(f"%{name}%"))
        count_query = count_query.where(TimeSeries.name.ilike(f"%{name}%"))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(TimeSeries.created_at.desc())
    
    result = await db.execute(query)
    series = result.scalars().all()
    
    # Convert to response
    series_list = []
    for ts in series:
        series_list.append(TimeSeriesResponse(
            id=ts.id,
            name=ts.name,
            values=ts.values,
            start_period={
                "year": ts.start_year,
                "period": ts.start_period,
                "frequency": ts.frequency
            },
            frequency=TsFrequency(ts.frequency),
            metadata=ts.metadata,
            created_at=ts.created_at,
            updated_at=ts.updated_at
        ))
    
    return TimeSeriesListResponse(
        series=series_list,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/timeseries/batch", response_model=list[TimeSeriesResponse])
async def batch_create_timeseries(
    request: BatchCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create multiple time series in a batch."""
    responses = []
    
    for series_request in request.series:
        # Validate each series
        ts_data = TsData(
            values=series_request.values,
            start_period=TsPeriod(
                year=series_request.start_period.year,
                period=series_request.start_period.period,
                frequency=series_request.start_period.frequency
            ),
            frequency=series_request.frequency,
            metadata=series_request.metadata
        )
        
        is_valid, errors, _ = validate_timeseries(ts_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid time series '{series_request.name}': {', '.join(errors)}"
            )
        
        # Create database record
        ts = TimeSeries(
            name=series_request.name,
            frequency=series_request.frequency.value,
            start_year=series_request.start_period.year,
            start_period=series_request.start_period.period,
            values=series_request.values,
            metadata=series_request.metadata
        )
        
        db.add(ts)
    
    # Commit all at once
    await db.commit()
    
    # Refresh and return
    for ts in db.new:
        await db.refresh(ts)
        responses.append(TimeSeriesResponse(
            id=ts.id,
            name=ts.name,
            values=ts.values,
            start_period={
                "year": ts.start_year,
                "period": ts.start_period,
                "frequency": ts.frequency
            },
            frequency=TsFrequency(ts.frequency),
            metadata=ts.metadata,
            created_at=ts.created_at,
            updated_at=ts.updated_at
        ))
    
    return responses