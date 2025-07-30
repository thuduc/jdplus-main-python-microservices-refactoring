"""X-13 API endpoints."""

import time
import pickle
from uuid import UUID, uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from jdemetra_common.models import TsData, TsPeriod, TsFrequency
from ..schemas.requests import ProcessRequest, DiagnosticsRequest, CompareRequest
from ..schemas.responses import (
    ProcessResponse, DiagnosticsResponse, CompareResponse,
    RegArimaResults, X11Results, SeatsDecomposition,
    ComparisonResult
)
from ..schemas.specification import X13Specification
from ..core.x13_wrapper import X13Processor
from ..core.diagnostics import run_diagnostics
from ..main import get_redis

router = APIRouter()


@router.post("/x13/process")
async def process(request: ProcessRequest, redis=Depends(get_redis)):
    """Process time series with X-13."""
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
        specification = request.specification or X13Specification()
        
        if request.async_processing:
            # In production, would submit to Celery
            # Here we simulate async processing
            job_id = uuid4()
            return {
                "job_id": str(job_id),
                "status": "pending",
                "message": "Processing job submitted"
            }
        
        # Process synchronously
        start_time = time.time()
        
        # Process with X-13
        processor = X13Processor(specification)
        results = processor.process(ts_data)
        
        processing_time = time.time() - start_time
        
        # Store results
        result_id = uuid4()
        await redis.setex(
            f"x13_result:{result_id}",
            86400,  # 24 hours
            pickle.dumps(results)
        )
        
        # Format response
        response = ProcessResponse(
            result_id=result_id,
            status="completed",
            regarima_results=RegArimaResults(
                model=results["regarima_results"]["model"].to_dict(),
                regression_effects=results["regarima_results"]["regression_effects"],
                outliers=results["regarima_results"]["outliers"],
                transformation=results["regarima_results"]["transformation"]
            ),
            processing_time=processing_time,
            specification_used=results["specification_used"]
        )
        
        if results.get("x11_results"):
            response.x11_results = X11Results(**results["x11_results"])
        
        if results.get("seats_results"):
            response.seats_results = SeatsDecomposition(**results["seats_results"])
        
        if results.get("forecasts"):
            response.forecasts = results["forecasts"]
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/x13/results/{result_id}")
async def get_results(result_id: UUID, redis=Depends(get_redis)):
    """Get processing results."""
    # Check cache
    cached = await redis.get(f"x13_result:{result_id}")
    
    if not cached:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = pickle.loads(cached)
    
    response = ProcessResponse(
        result_id=result_id,
        status="completed",
        regarima_results=RegArimaResults(
            model=results["regarima_results"]["model"].to_dict(),
            regression_effects=results["regarima_results"]["regression_effects"],
            outliers=results["regarima_results"]["outliers"],
            transformation=results["regarima_results"]["transformation"]
        ),
        specification_used=results["specification_used"]
    )
    
    if results.get("x11_results"):
        response.x11_results = X11Results(**results["x11_results"])
    
    if results.get("seats_results"):
        response.seats_results = SeatsDecomposition(**results["seats_results"])
    
    if results.get("forecasts"):
        response.forecasts = results["forecasts"]
    
    return response


@router.post("/x13/specification")
async def create_specification(specification: X13Specification):
    """Create or validate an X-13 specification."""
    # Validate specification
    spec_dict = specification.dict()
    
    # Could store named specifications here
    spec_id = uuid4()
    
    return {
        "specification_id": spec_id,
        "specification": spec_dict,
        "valid": True,
        "warnings": []
    }


@router.post("/x13/diagnostics", response_model=DiagnosticsResponse)
async def diagnostics(request: DiagnosticsRequest, redis=Depends(get_redis)):
    """Run diagnostics on X-13 results."""
    try:
        # Retrieve results
        cached = await redis.get(f"x13_result:{request.result_id}")
        
        if not cached:
            raise HTTPException(status_code=404, detail="Results not found")
        
        results = pickle.loads(cached)
        
        # Run diagnostics
        diagnostic_results = run_diagnostics(results, request.tests)
        
        return DiagnosticsResponse(
            result_id=request.result_id,
            spectrum_analysis=diagnostic_results.get("spectrum_analysis"),
            stability_tests=diagnostic_results.get("stability_tests"),
            residual_diagnostics=diagnostic_results.get("residual_diagnostics"),
            sliding_spans=diagnostic_results.get("sliding_spans"),
            summary_statistics=diagnostic_results["summary_statistics"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/x13/compare", response_model=CompareResponse)
async def compare_specifications(request: CompareRequest):
    """Compare multiple X-13 specifications."""
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
        
        # Process with each specification
        results = []
        for i, spec in enumerate(request.specifications):
            processor = X13Processor(spec)
            result = processor.process(ts_data)
            
            # Extract comparison metrics
            model = result["regarima_results"]["model"]
            
            # Run diagnostics for Ljung-Box
            diag_results = run_diagnostics(result, ["residuals"])
            ljung_box_pvalue = diag_results["residual_diagnostics"]["autocorrelation"]["p_value"]
            
            # Stability score (simplified)
            stability_diag = run_diagnostics(result, ["stability"])
            stability_score = 1.0 if stability_diag["stability_tests"]["variance_stability"]["stable"] else 0.5
            
            results.append(ComparisonResult(
                specification_index=i,
                aic=float(model.aic) if model.aic else None,
                bic=float(model.bic) if model.bic else None,
                ljung_box_pvalue=float(ljung_box_pvalue),
                stability_score=float(stability_score)
            ))
        
        # Rank specifications
        # Simple ranking based on AIC
        if "aic" in request.comparison_criteria:
            sorted_indices = sorted(range(len(results)), key=lambda i: results[i].aic or float('inf'))
            for rank, idx in enumerate(sorted_indices):
                results[idx].rank = rank + 1
            best_idx = sorted_indices[0]
        else:
            # Default to first specification
            best_idx = 0
            for i, r in enumerate(results):
                r.rank = i + 1
        
        comparison_id = uuid4()
        
        return CompareResponse(
            comparison_id=comparison_id,
            results=results,
            best_specification_index=best_idx,
            comparison_summary={
                "n_specifications": len(request.specifications),
                "criteria_used": request.comparison_criteria,
                "best_aic": min(r.aic for r in results if r.aic),
                "all_pass_ljung_box": all(r.ljung_box_pvalue > 0.05 for r in results if r.ljung_box_pvalue)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))