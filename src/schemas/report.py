from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict


class ReportBase(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_mb: Optional[float] = None
    memory_total_mb: Optional[float] = None
    disk_percent: float
    disk_used_gb: Optional[float] = None
    disk_total_gb: Optional[float] = None
    network: Optional[Dict] = None


class ReportCreate(ReportBase):
    pass


class ReportResponse(ReportBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int
