from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from src.models.order import OrderStatus


class OrderBase(BaseModel):
    quantity: int
    supplier: str
    total_cost: float = 0.0
    notes: Optional[str] = None
    medication_id: int

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    quantity: Optional[int] = None
    status: Optional[OrderStatus] = None
    received_date: Optional[datetime] = None
    supplier: Optional[str] = None
    total_cost: Optional[float] = None
    notes: Optional[str] = None

class OrderResponse(OrderBase):
    id: int
    status: OrderStatus
    order_date: datetime
    received_date: Optional[datetime] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    received_date: Optional[datetime] = None
