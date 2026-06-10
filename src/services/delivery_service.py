from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
import logging

from src.models.delivery import Delivery, DeliveryCreate, DeliveryUpdate, DeliveryStatus
from src.models.supplier import Supplier
from src.exceptions import DeliveryNotFoundError, SupplierNotFoundError

logger = logging.getLogger(__name__)


def _query_with_relations(db: Session):
    return db.query(Delivery).options(joinedload(Delivery.supplier), joinedload(Delivery.medication))


def get_deliveries(
    db: Session,
    status_filter: Optional[DeliveryStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Delivery]:
    query = _query_with_relations(db)
    if status_filter is not None:
        query = query.filter(Delivery.status == status_filter)
    return query.order_by(Delivery.created_at.desc()).offset(skip).limit(limit).all()


def get_delivery_by_id(db: Session, delivery_id: int) -> Optional[Delivery]:
    return _query_with_relations(db).filter(Delivery.id == delivery_id).first()


def create_delivery(db: Session, data: DeliveryCreate) -> Delivery:
    supplier = db.get(Supplier, data.supplier_id)
    if not supplier:
        raise SupplierNotFoundError(data.supplier_id)

    delivery = Delivery(**data.model_dump(), status=DeliveryStatus.IN_TRANSIT)
    db.add(delivery)
    try:
        db.commit()
        db.refresh(delivery)
    except Exception:
        db.rollback()
        raise
    return get_delivery_by_id(db, delivery.id)


def update_delivery(db: Session, delivery_id: int, data: DeliveryUpdate) -> Delivery:
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise DeliveryNotFoundError(delivery_id)

    update_dict = data.model_dump(exclude_unset=True)
    new_status = update_dict.get("status")
    for key, value in update_dict.items():
        setattr(delivery, key, value)
    if new_status == DeliveryStatus.RECEIVED and not delivery.received_at:
        delivery.received_at = datetime.utcnow()
    delivery.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(delivery)
    except Exception:
        db.rollback()
        raise
    return get_delivery_by_id(db, delivery.id)


def delete_delivery(db: Session, delivery_id: int) -> None:
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise DeliveryNotFoundError(delivery_id)
    db.delete(delivery)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
