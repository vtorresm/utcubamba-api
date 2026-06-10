from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class AuditStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    REJECTED = "rejected"


class AuditBase(SQLModel):
    sector: str = Field(..., max_length=150, nullable=False)
    audit_date: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    documentation_score: float = Field(default=0.0, ge=0)
    precision_score: float = Field(default=0.0, ge=0, le=1)
    status: AuditStatus = Field(default=AuditStatus.IN_PROGRESS, nullable=False)
    notes: Optional[str] = Field(default=None, max_length=1000)
    responsible_id: int = Field(foreign_key="users.id", nullable=False)


class Audit(AuditBase, table=True):
    __tablename__ = "audits"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    responsible: "User" = Relationship()


class UserMini(SQLModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True


class AuditCreate(SQLModel):
    sector: str
    documentation_score: float = 0.0
    precision_score: float = 0.0
    notes: Optional[str] = None


class AuditUpdate(SQLModel):
    sector: Optional[str] = None
    documentation_score: Optional[float] = None
    precision_score: Optional[float] = None
    status: Optional[AuditStatus] = None
    notes: Optional[str] = None


class AuditInDB(AuditBase):
    id: int
    created_at: datetime
    updated_at: datetime
    responsible: Optional[UserMini] = None

    class Config:
        from_attributes = True
