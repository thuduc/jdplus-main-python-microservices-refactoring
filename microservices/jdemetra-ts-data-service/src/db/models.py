"""Database models."""

from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

from .connection import Base


class TimeSeries(Base):
    """Time series database model."""
    
    __tablename__ = "timeseries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    frequency = Column(String, nullable=False)
    start_year = Column(Integer, nullable=False)
    start_period = Column(Integer, nullable=False)
    values = Column(ARRAY(Float), nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_timeseries_name", "name"),
        Index("idx_timeseries_frequency", "frequency"),
        Index("idx_timeseries_created_at", "created_at"),
    )