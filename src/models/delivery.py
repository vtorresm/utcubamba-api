from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .supplier import Supplier
    from .medication import Medication


class DeliveryStatus(str, Enum):
    IN_TRANSIT = "in_transit"
    PENDING_INSPECTION = "pending_inspection"
    RECEIVED = "received"


class DeliveryBase(SQLModel):
    supplier_id: int = Field(foreign_key="suppliers.id", nullable=False)
    medication_id: Optional[int] = Field(default=None, foreign_key="medications.id")
    product: str = Field(..., max_length=250, nullable=False)
    quantity: int = Field(default=0, ge=0)
    status: DeliveryStatus = Field(default=DeliveryStatus.IN_TRANSIT, nullable=False)
    eta: Optional[datetime] = Field(default=None)
    received_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=1000)


class Delivery(DeliveryBase, table=True):
    __tablename__ = "deliveries"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    supplier: "Supplier" = Relationship()
    medication: Optional["Medication"] = Relationship()


class SupplierMini(SQLModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MedicationMini(SQLModel):
    id: int
    name: str
    unit: str

    class Config:
        from_attributes = True


class DeliveryCreate(SQLModel):
    supplier_id: int
    medication_id: Optional[int] = None
    product: str
    quantity: int = 0
    eta: Optional[datetime] = None
    notes: Optional[str] = None


class DeliveryUpdate(SQLModel):
    product: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[DeliveryStatus] = None
    eta: Optional[datetime] = None
    received_at: Optional[datetime] = None
    notes: Optional[str] = None


class DeliveryInDB(DeliveryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    supplier: Optional[SupplierMini] = None
    medication: Optional[MedicationMini] = None

    class Config:
        from_attributes = True
