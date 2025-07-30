"""ARIMA API endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from jdemetra_common.models import TsData, TsPeriod, TsFrequency, ArimaOrder
from ..schemas.requests import (
    EstimateRequest, ForecastRequest, IdentifyRequest, DiagnoseRequest
)
from ..schemas.responses import (
    EstimateResponse, ForecastResponse, IdentifyResponse, DiagnoseResponse,
    ForecastPoint, DiagnosticTest
)
from ..core.arima_estimation import estimate_arima, identify_arima
from ..core.forecasting import generate_forecasts
from ..core.diagnostics import run_diagnostics
from ..models.storage import ModelStorage
from ..main import get_redis

router = APIRouter()


@router.post("/arima/estimate", response_model=EstimateResponse)
async def estimate_model(request: EstimateRequest, redis=Depends(get_redis)):
    """Estimate ARIMA model."""
    try:
        # Convert request to TsData
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
        
        # Convert order if provided
        order = None
        if request.order:
            order = ArimaOrder(
                p=request.order.p,
                d=request.order.d,
                q=request.order.q,
                seasonal_p=request.order.seasonal_p,
                seasonal_d=request.order.seasonal_d,
                seasonal_q=request.order.seasonal_q,
                seasonal_period=request.order.seasonal_period
            )
        
        # Estimate model
        model, fitting_info = estimate_arima(
            ts_data, order, request.method, request.include_mean
        )
        
        # Save model
        storage = ModelStorage(redis)
        model_id = await storage.save_model(model, ts_data)
        
        return EstimateResponse(
            model_id=model_id,
            model=model.to_dict(),
            fit_time=fitting_info["fit_time"],
            in_sample_metrics=fitting_info["in_sample_metrics"],
            convergence_info=fitting_info["convergence"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/arima/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest, redis=Depends(get_redis)):
    """Generate forecasts from saved model."""
    try:
        # Retrieve model
        storage = ModelStorage(redis)
        model_data = await storage.get_model(request.model_id)
        
        if not model_data:
            raise HTTPException(status_code=404, detail="Model not found")
        
        model, ts_data = model_data
        
        # Generate forecasts
        forecasts, forecast_time = generate_forecasts(
            ts_data, model, request.horizon, request.confidence_level
        )
        
        # Convert to response format
        forecast_points = []
        for f in forecasts:
            forecast_points.append(ForecastPoint(**f))
        
        return ForecastResponse(
            model_id=request.model_id,
            forecasts=forecast_points,
            confidence_level=request.confidence_level,
            forecast_time=forecast_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/arima/identify", response_model=IdentifyResponse)
async def identify(request: IdentifyRequest):
    """Automatically identify best ARIMA model."""
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
        
        # Identify model
        best_model, search_info = identify_arima(
            ts_data,
            seasonal=request.seasonal,
            stepwise=request.stepwise,
            max_p=request.max_p,
            max_q=request.max_q,
            max_d=request.max_d,
            information_criterion=request.information_criterion
        )
        
        return IdentifyResponse(
            best_model=best_model.to_dict(),
            search_summary=search_info["search_summary"],
            candidates_evaluated=search_info["candidates_evaluated"],
            identification_time=search_info["identification_time"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/arima/model/{model_id}")
async def get_model(model_id: UUID, redis=Depends(get_redis)):
    """Retrieve saved model."""
    storage = ModelStorage(redis)
    model_data = await storage.get_model(model_id)
    
    if not model_data:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model, ts_data = model_data
    
    return {
        "model_id": model_id,
        "model": model.to_dict(),
        "timeseries_info": {
            "length": ts_data.length,
            "frequency": ts_data.frequency.value,
            "start_period": {
                "year": ts_data.start_period.year,
                "period": ts_data.start_period.period
            }
        }
    }


@router.post("/arima/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: DiagnoseRequest, redis=Depends(get_redis)):
    """Run diagnostics on saved model."""
    try:
        # Retrieve model
        storage = ModelStorage(redis)
        model_data = await storage.get_model(request.model_id)
        
        if not model_data:
            raise HTTPException(status_code=404, detail="Model not found")
        
        model, ts_data = model_data
        
        # Run diagnostics
        results = run_diagnostics(ts_data, model, request.tests)
        
        # Convert to response format
        diagnostic_tests = []
        for test in results["diagnostic_tests"]:
            diagnostic_tests.append(DiagnosticTest(**test))
        
        return DiagnoseResponse(
            model_id=request.model_id,
            residual_stats=results["residual_stats"],
            diagnostic_tests=diagnostic_tests,
            model_adequacy=results["model_adequacy"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))