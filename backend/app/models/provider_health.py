import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class ProviderHealth(Base):
    __tablename__ = "provider_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    provider_name = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False) # 'HEALTHY', 'DEGRADED', 'RATE_LIMITED', 'EXHAUSTED', 'OFFLINE'
    
    quota_remaining = Column(Float, nullable=True)
    rpm_remaining = Column(Integer, nullable=True)
    tpm_remaining = Column(Integer, nullable=True)
    
    error_count = Column(Integer, default=0)
    failure_rate = Column(Float, default=0.0)
    
    average_latency_ms = Column(Float, nullable=True)
    
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
