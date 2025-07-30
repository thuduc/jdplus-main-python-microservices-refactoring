"""Celery tasks for asynchronous processing."""

from celery import Celery
from uuid import uuid4
import pickle

from ..core.config import settings
from ..core.tramo import TramoProcessor
from ..core.seats import SeatsDecomposer
from ..schemas.specification import TramoSeatsSpecification
from jdemetra_common.models import TsData

# Initialize Celery
celery_app = Celery(
    'tramoseats',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='pickle',
    accept_content=['pickle'],
    result_serializer='pickle',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(bind=True, max_retries=3)
def process_tramoseats_async(self, ts_data_dict: dict, specification_dict: dict):
    """Asynchronously process TRAMO/SEATS."""
    try:
        # Reconstruct objects
        ts_data = TsData.from_dict(ts_data_dict)
        specification = TramoSeatsSpecification(**specification_dict)
        
        # Process with TRAMO
        tramo_processor = TramoProcessor(specification)
        tramo_results = tramo_processor.process(ts_data)
        
        # Process with SEATS
        seats_decomposer = SeatsDecomposer(specification.decomposition)
        seats_results = seats_decomposer.decompose(ts_data, tramo_results)
        
        # Store results
        result_id = uuid4()
        result_data = {
            "result_id": str(result_id),
            "status": "completed",
            "tramo_results": tramo_results,
            "seats_results": seats_results,
            "specification_used": specification_dict
        }
        
        return result_data
        
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))