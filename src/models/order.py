from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .medication import Medication

class OrderStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SHIPPED = "shipped"
    RECEIVED = "received"
    CANCELLED = "cancelled"

class OrderBase(SQLModel):
    quantity: int = Field(..., gt=0, nullable=False)
    status: OrderStatus = Field(default=OrderStatus.PENDING, nullable=False)
    order_date: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    received_date: Optional[datetime] = Field(default=None)
    supplier: str = Field(..., max_length=200, nullable=False)
    total_cost: float = Field(default=0.0, ge=0)
    notes: Optional[str] = Field(default=None, max_length=1000)
    medication_id: int = Field(foreign_key="medications.id", nullable=False)
    created_by: int = Field(foreign_key="users.id", nullable=False)

class Order(OrderBase, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    medication: "Medication" = Relationship(back_populates="orders")
    creator: "User" = Relationship(back_populates="orders")

class OrderCreate(SQLModel):
    quantity: int
    supplier: str
    total_cost: float = 0.0
    notes: Optional[str] = None
    medication_id: int

class OrderUpdate(SQLModel):
    quantity: Optional[int] = None
    status: Optional[OrderStatus] = None
    received_date: Optional[datetime] = None
    supplier: Optional[str] = None
    total_cost: Optional[float] = None
    notes: Optional[str] = None

class OrderInDB(OrderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
