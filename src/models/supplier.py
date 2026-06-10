from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field


class SupplierStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SupplierBase(SQLModel):
    name: str = Field(..., max_length=200, nullable=False)
    category: Optional[str] = Field(default=None, max_length=100)
    contact_name: Optional[str] = Field(default=None, max_length=150)
    contact_email: Optional[str] = Field(default=None, max_length=150)
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    reliability_score: float = Field(default=0.0, ge=0, le=100)
    quality_score: float = Field(default=0.0, ge=0, le=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: SupplierStatus = Field(default=SupplierStatus.ACTIVE, nullable=False)


class Supplier(SupplierBase, table=True):
    __tablename__ = "suppliers"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SupplierCreate(SQLModel):
    name: str
    category: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    reliability_score: float = 0.0
    quality_score: float = 0.0
    description: Optional[str] = None


class SupplierUpdate(SQLModel):
    name: Optional[str] = None
    category: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    reliability_score: Optional[float] = None
    quality_score: Optional[float] = None
    description: Optional[str] = None
    status: Optional[SupplierStatus] = None


class SupplierInDB(SupplierBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
