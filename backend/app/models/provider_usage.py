import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class ProviderUsage(Base):
    __tablename__ = "provider_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    provider_name = Column(String, index=True, nullable=False)
    model = Column(String, nullable=False)
    tokens_used = Column(Integer, nullable=False, default=0)
    requests_count = Column(Integer, nullable=False, default=1)
    failures_count = Column(Integer, nullable=False, default=0)
    date = Column(DateTime, default=datetime.utcnow, nullable=False) # For daily quotas
