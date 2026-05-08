from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Float, JSON, DateTime
from sqlalchemy.orm import relationship
from src.core.database import Base


class ServerReport(Base):
    __tablename__ = "server_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    memory_used_mb = Column(Float, nullable=True)
    memory_total_mb = Column(Float, nullable=True)
    disk_percent = Column(Float, nullable=False)
    disk_used_gb = Column(Float, nullable=True)
    disk_total_gb = Column(Float, nullable=True)
    network = Column(JSON, nullable=True)  # store bytes sent/received
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to User (optional, for ORM queries)
    user = relationship("User", back_populates="reports")
