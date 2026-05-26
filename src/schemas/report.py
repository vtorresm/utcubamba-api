from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from src.models.report import ReportType, ReportFormat, ReportStatus


class ReportBase(BaseModel):
    title: str
    type: ReportType
    format: ReportFormat = ReportFormat.PDF
    parameters: Optional[dict] = None

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    data: Optional[dict] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None

class ReportResponse(ReportBase):
    id: int
    status: ReportStatus
    data: Optional[dict] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    generated_by: int
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
