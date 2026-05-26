from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from src.models.order import Order, OrderCreate, OrderUpdate, OrderStatus
from src.models.medication import Medication
from src.models.user import User

logger = logging.getLogger(__name__)


def create_order(
    db: Session,
    order_data: OrderCreate,
    user: User
) -> Order:
    medication = db.get(Medication, order_data.medication_id)
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicamento con ID {order_data.medication_id} no encontrado"
        )

    order = Order(
        medication_id=order_data.medication_id,
        quantity=order_data.quantity,
        supplier=order_data.supplier,
        total_cost=order_data.total_cost,
        notes=order_data.notes,
        created_by=user.id,
        status=OrderStatus.PENDING,
        order_date=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_orders(
    db: Session,
    medication_id: Optional[int] = None,
    status_filter: Optional[OrderStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Order]:
    query = db.query(Order)
    if medication_id is not None:
        query = query.filter(Order.medication_id == medication_id)
    if status_filter is not None:
        query = query.filter(Order.status == status_filter)
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    return db.get(Order, order_id)


def get_orders_by_medication(
    db: Session,
    medication_id: int,
    skip: int = 0,
    limit: int = 50
) -> List[Order]:
    return db.query(Order).filter(
        Order.medication_id == medication_id
    ).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def update_order_status(
    db: Session,
    order_id: int,
    new_status: OrderStatus,
    received_date: Optional[datetime] = None
) -> Optional[Order]:
    order = db.get(Order, order_id)
    if not order:
        return None

    order.status = new_status
    if received_date:
        order.received_date = received_date
    elif new_status == OrderStatus.RECEIVED:
        order.received_date = datetime.utcnow()

    if new_status == OrderStatus.RECEIVED:
        medication = db.get(Medication, order.medication_id)
        if medication:
            medication.stock += order.quantity

    db.commit()
    db.refresh(order)
    return order


def update_order(
    db: Session,
    order_id: int,
    update_data: OrderUpdate
) -> Optional[Order]:
    order = db.get(Order, order_id)
    if not order:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(order, key, value)
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order_id: int) -> bool:
    order = db.get(Order, order_id)
    if not order:
        return False
    db.delete(order)
    db.commit()
    return True
