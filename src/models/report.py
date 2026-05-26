from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .user import User

class ReportType(str, Enum):
    INVENTORY = "inventory"
    MOVEMENTS = "movements"
    TRENDS = "trends"
    ALERTS = "alerts"
    FINANCIAL = "financial"
    PATIENTS = "patients"

class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"

class ReportStatus(str, Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportBase(SQLModel):
    title: str = Field(..., max_length=200, nullable=False)
    type: ReportType = Field(..., nullable=False)
    format: ReportFormat = Field(default=ReportFormat.PDF, nullable=False)
    status: ReportStatus = Field(default=ReportStatus.GENERATING, nullable=False)
    parameters: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    data: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    file_path: Optional[str] = Field(default=None, max_length=500)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    generated_by: int = Field(foreign_key="users.id", nullable=False)
    generated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class Report(ReportBase, table=True):
    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    generator: "User" = Relationship(back_populates="reports")

class ReportCreate(SQLModel):
    title: str
    type: ReportType
    format: ReportFormat = ReportFormat.PDF
    parameters: Optional[dict] = None

class ReportUpdate(SQLModel):
    status: Optional[ReportStatus] = None
    data: Optional[dict] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None

class ReportInDB(ReportBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
