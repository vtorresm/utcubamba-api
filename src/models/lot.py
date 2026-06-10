from datetime import datetime, date
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .medication import Medication


class LotStatus(str, Enum):
    RECEIVED = "received"
    QUALITY_CHECK = "quality_check"
    STORED = "stored"
    DISPATCHED = "dispatched"


# ─── Lot ──────────────────────────────────────────────────────────────────────

class LotBase(SQLModel):
    code: str = Field(..., max_length=50, nullable=False, index=True)
    medication_id: int = Field(foreign_key="medications.id", nullable=False)
    quantity: int = Field(default=0, ge=0)
    location: Optional[str] = Field(default=None, max_length=150)
    temperature: Optional[float] = Field(default=None)
    humidity: Optional[float] = Field(default=None)
    manufactured_date: Optional[date] = Field(default=None)
    expiration_date: Optional[date] = Field(default=None)
    status: LotStatus = Field(default=LotStatus.RECEIVED, nullable=False)
    notes: Optional[str] = Field(default=None, max_length=1000)


class Lot(LotBase, table=True):
    __tablename__ = "lots"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    medication: "Medication" = Relationship()
    events: List["LotEvent"] = Relationship(
        back_populates="lot",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "LotEvent.step_order"},
    )


# ─── Lot Event (pasos de trazabilidad) ───────────────────────────────────────

class LotEventBase(SQLModel):
    lot_id: int = Field(foreign_key="lots.id", nullable=False)
    title: str = Field(..., max_length=200, nullable=False)
    detail: Optional[str] = Field(default=None, max_length=500)
    event_date: Optional[datetime] = Field(default=None)
    completed: bool = Field(default=False, nullable=False)
    step_order: int = Field(default=0, nullable=False)


class LotEvent(LotEventBase, table=True):
    __tablename__ = "lot_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    lot: "Lot" = Relationship(back_populates="events")


# ─── Schemas ──────────────────────────────────────────────────────────────────

class MedicationMini(SQLModel):
    id: int
    name: str
    unit: str

    class Config:
        from_attributes = True


class LotEventCreate(SQLModel):
    title: str
    detail: Optional[str] = None
    event_date: Optional[datetime] = None
    completed: bool = False
    step_order: int = 0


class LotEventInDB(LotEventBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LotCreate(SQLModel):
    code: str
    medication_id: int
    quantity: int = 0
    location: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    manufactured_date: Optional[date] = None
    expiration_date: Optional[date] = None
    notes: Optional[str] = None


class LotUpdate(SQLModel):
    quantity: Optional[int] = None
    location: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    status: Optional[LotStatus] = None
    notes: Optional[str] = None


class LotInDB(LotBase):
    id: int
    created_at: datetime
    updated_at: datetime
    medication: Optional[MedicationMini] = None
    events: List[LotEventInDB] = []

    class Config:
        from_attributes = True
