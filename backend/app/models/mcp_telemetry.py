import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class MCPTelemetry(Base):
    """
    Stores telemetry for MCP tool usage to track performance, latency,
    and agent workflows over time.
    """
    __tablename__ = "mcp_telemetry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tool_name = Column(String(255), nullable=False, index=True)
    query = Column(String, nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    latency_ms = Column(Float, nullable=False)
    memory_count = Column(Integer, nullable=False, default=0)
    avg_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
