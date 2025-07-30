"""Statistical analysis API endpoints."""

import numpy as np
from fastapi import APIRouter, HTTPException

from ..schemas.requests import (
    NormalityTestRequest, StationarityTestRequest, DescriptiveStatsRequest,
    DistributionFitRequest, RandomnessTestRequest, SeasonalityTestRequest
)
from ..schemas.responses import (
    TestResult, DescriptiveStatsResponse, 
    DistributionFitResponse, DistributionFitListResponse
)
from ..core.tests import (
    normality_test, stationarity_test, randomness_test, seasonality_test
)
from ..core.descriptive import compute_descriptive_stats
from ..core.distributions import fit_multiple_distributions

router = APIRouter()


def interpret_test_result(test_name: str, p_value: float, reject_null: bool, 
                         null_hypothesis: str = None) -> str:
    """Generate human-readable interpretation of test result."""
    if test_name == "normality":
        if reject_null:
            return f"Data is not normally distributed (p-value: {p_value:.4f})"
        else:
            return f"Data appears to be normally distributed (p-value: {p_value:.4f})"
    elif test_name == "stationarity":
        if reject_null:
            return f"Data is stationary (p-value: {p_value:.4f})"
        else:
            return f"Data is non-stationary (p-value: {p_value:.4f})"
    elif test_name == "randomness":
        if reject_null:
            return f"Data shows non-random patterns (p-value: {p_value:.4f})"
        else:
            return f"Data appears to be random (p-value: {p_value:.4f})"
    elif test_name == "seasonality":
        if reject_null:
            return f"Significant seasonality detected (p-value: {p_value:.4f})"
        else:
            return f"No significant seasonality detected (p-value: {p_value:.4f})"
    else:
        return f"Test result: p-value = {p_value:.4f}, reject null = {reject_null}"


@router.post("/stats/test/normality", response_model=TestResult)
async def test_normality(request: NormalityTestRequest):
    """Test data for normality."""
    try:
        data = np.array(request.data)
        statistic, p_value, info = normality_test(data, request.method)
        
        reject_null = p_value < 0.05
        interpretation = interpret_test_result("normality", p_value, reject_null)
        
        return TestResult(
            statistic=float(statistic),
            p_value=float(p_value),
            reject_null=reject_null,
            interpretation=interpretation,
            additional_info=info
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stats/test/stationarity", response_model=TestResult)
async def test_stationarity(request: StationarityTestRequest):
    """Test data for stationarity."""
    try:
        data = np.array(request.data)
        statistic, p_value, info = stationarity_test(
            data, request.method, request.regression, request.max_lag
        )
        
        # For ADF/PP, reject null means stationary
        # For KPSS, reject null means non-stationary
        if request.method == "kpss":
            reject_null = p_value < 0.05
            is_stationary = not reject_null
        else:
            reject_null = p_value < 0.05
            is_stationary = reject_null
        
        interpretation = interpret_test_result("stationarity", p_value, is_stationary)
        
        return TestResult(
            statistic=float(statistic),
            p_value=float(p_value),
            reject_null=reject_null,
            interpretation=interpretation,
            additional_info=info
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stats/descriptive", response_model=DescriptiveStatsResponse)
async def compute_descriptive(request: DescriptiveStatsRequest):
    """Compute descriptive statistics."""
    try:
        data = np.array(request.data)
        stats_dict = compute_descriptive_stats(data, request.percentiles)
        
        return DescriptiveStatsResponse(**stats_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stats/distribution/fit", response_model=DistributionFitListResponse)
async def fit_distributions(request: DistributionFitRequest):
    """Fit distributions to data."""
    try:
        data = np.array(request.data)
        results = fit_multiple_distributions(data, request.distributions)
        
        if not results:
            raise HTTPException(status_code=400, detail="No distributions could be fitted")
        
        response_results = []
        for r in results:
            response_results.append(DistributionFitResponse(
                distribution=r["distribution"],
                parameters=r["parameters"],
                goodness_of_fit=r["goodness_of_fit"],
                best_fit=r["best_fit"]
            ))
        
        best_dist = results[0]["distribution"]
        
        return DistributionFitListResponse(
            results=response_results,
            best_distribution=best_dist
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stats/test/randomness", response_model=TestResult)
async def test_randomness(request: RandomnessTestRequest):
    """Test data for randomness."""
    try:
        data = np.array(request.data)
        statistic, p_value, info = randomness_test(data, request.method, request.lags)
        
        reject_null = p_value < 0.05
        interpretation = interpret_test_result("randomness", p_value, reject_null)
        
        return TestResult(
            statistic=float(statistic),
            p_value=float(p_value),
            reject_null=reject_null,
            interpretation=interpretation,
            additional_info=info
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stats/test/seasonality", response_model=TestResult)
async def test_seasonality(request: SeasonalityTestRequest):
    """Test data for seasonality."""
    try:
        data = np.array(request.data)
        statistic, p_value, info = seasonality_test(data, request.period, request.method)
        
        reject_null = p_value < 0.05
        interpretation = interpret_test_result("seasonality", p_value, reject_null)
        
        return TestResult(
            statistic=float(statistic),
            p_value=float(p_value),
            reject_null=reject_null,
            interpretation=interpretation,
            additional_info=info
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))