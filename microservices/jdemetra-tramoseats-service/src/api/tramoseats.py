"""TRAMO/SEATS API endpoints."""

import time
import pickle
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from ..schemas.requests import ProcessRequest, DiagnosticsRequest
from ..schemas.responses import (
    ProcessResponse, AsyncProcessResponse, DiagnosticsResponse,
    TramoResults, SeatsResults, SeatsComponent
)
from ..schemas.specification import TramoSeatsSpecification
from ..core.tramo import TramoProcessor
from ..core.seats import SeatsDecomposer
from ..core.diagnostics import run_diagnostics
from ..tasks.processing import process_tramoseats_async
from ..main import get_redis

router = APIRouter()


@router.post("/tramoseats/process")
async def process(request: ProcessRequest, redis=Depends(get_redis)):
    """Process time series with TRAMO/SEATS."""
    try:
        # Convert to TsData
        ts_data = TsData(
            values=request.timeseries.values,
            start_period=TsPeriod(
                year=request.timeseries.start_period.year,
                period=request.timeseries.start_period.period,
                frequency=request.timeseries.start_period.frequency
            ),
            frequency=request.timeseries.frequency,
            metadata=request.timeseries.metadata
        )
        
        # Use default specification if not provided
        specification = request.specification or TramoSeatsSpecification()
        
        if request.async_processing:
            # Submit to Celery
            task = process_tramoseats_async.delay(
                ts_data.to_dict(),
                specification.dict()
            )
            
            return AsyncProcessResponse(
                job_id=task.id,
                status="pending",
                message="Processing job submitted"
            )
        
        # Process synchronously
        start_time = time.time()
        
        # Process with TRAMO
        tramo_processor = TramoProcessor(specification)
        tramo_results = tramo_processor.process(ts_data)
        
        # Process with SEATS
        seats_decomposer = SeatsDecomposer(specification.decomposition)
        seats_results = seats_decomposer.decompose(ts_data, tramo_results)
        
        processing_time = time.time() - start_time
        
        # Store results
        result_id = uuid4()
        result_data = {
            "ts_data": ts_data.to_dict(),
            "tramo_results": tramo_results,
            "seats_results": seats_results,
            "specification": specification.dict()
        }
        
        # Cache results
        await redis.setex(
            f"tramoseats_result:{result_id}",
            86400,  # 24 hours
            pickle.dumps(result_data)
        )
        
        # Format response
        return ProcessResponse(
            result_id=result_id,
            status="completed",
            tramo_results=TramoResults(
                model=tramo_results["model"].to_dict(),
                outliers=tramo_results["outliers"],
                calendar_effects=tramo_results["calendar_effects"],
                regression_effects=None,
                residuals=tramo_results["residuals"]
            ),
            seats_results=SeatsResults(
                trend=SeatsComponent(**seats_results["trend"]),
                seasonal=SeatsComponent(**seats_results["seasonal"]),
                irregular=SeatsComponent(**seats_results["irregular"]),
                seasonally_adjusted=seats_results["seasonally_adjusted"]
            ),
            processing_time=processing_time,
            specification_used=specification.dict()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tramoseats/results/{result_id}")
async def get_results(result_id: UUID, redis=Depends(get_redis)):
    """Get processing results."""
    # Check cache
    cached = await redis.get(f"tramoseats_result:{result_id}")
    
    if not cached:
        raise HTTPException(status_code=404, detail="Results not found")
    
    result_data = pickle.loads(cached)
    
    return ProcessResponse(
        result_id=result_id,
        status="completed",
        tramo_results=TramoResults(
            model=result_data["tramo_results"]["model"].to_dict(),
            outliers=result_data["tramo_results"]["outliers"],
            calendar_effects=result_data["tramo_results"]["calendar_effects"],
            regression_effects=None,
            residuals=result_data["tramo_results"]["residuals"]
        ),
        seats_results=SeatsResults(
            trend=SeatsComponent(**result_data["seats_results"]["trend"]),
            seasonal=SeatsComponent(**result_data["seats_results"]["seasonal"]),
            irregular=SeatsComponent(**result_data["seats_results"]["irregular"]),
            seasonally_adjusted=result_data["seats_results"]["seasonally_adjusted"]
        ),
        processing_time=None,
        specification_used=result_data["specification"]
    )


@router.post("/tramoseats/specification")
async def create_specification(specification: TramoSeatsSpecification):
    """Create or validate a TRAMO/SEATS specification."""
    # Validate specification
    spec_dict = specification.dict()
    
    # Could store named specifications here
    spec_id = uuid4()
    
    return {
        "specification_id": spec_id,
        "specification": spec_dict,
        "valid": True
    }


@router.post("/tramoseats/diagnostics", response_model=DiagnosticsResponse)
async def diagnostics(request: DiagnosticsRequest, redis=Depends(get_redis)):
    """Run diagnostics on TRAMO/SEATS results."""
    try:
        # Retrieve results
        cached = await redis.get(f"tramoseats_result:{request.result_id}")
        
        if not cached:
            raise HTTPException(status_code=404, detail="Results not found")
        
        result_data = pickle.loads(cached)
        
        # Reconstruct TsData
        ts_data = TsData.from_dict(result_data["ts_data"])
        
        # Run diagnostics
        diagnostic_results = run_diagnostics(
            ts_data,
            result_data["tramo_results"],
            result_data["seats_results"],
            request.tests
        )
        
        return DiagnosticsResponse(
            result_id=request.result_id,
            seasonality_tests=diagnostic_results.get("seasonality_tests"),
            residual_tests=diagnostic_results.get("residual_tests"),
            spectral_analysis=diagnostic_results.get("spectral_analysis"),
            quality_measures=diagnostic_results["quality_measures"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tramoseats/job/{job_id}")
async def get_job_status(job_id: str):
    """Get async job status."""
    from ..tasks.processing import celery_app
    
    result = celery_app.AsyncResult(job_id)
    
    if result.state == 'PENDING':
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Job is waiting to be processed"
        }
    elif result.state == 'FAILURE':
        return {
            "job_id": job_id,
            "status": "failed",
            "message": str(result.info)
        }
    elif result.state == 'SUCCESS':
        return {
            "job_id": job_id,
            "status": "completed",
            "result_id": result.result["result_id"],
            "message": "Processing completed"
        }
    else:
        return {
            "job_id": job_id,
            "status": result.state.lower(),
            "message": f"Job is {result.state}"
        }