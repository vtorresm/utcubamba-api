from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from src.models.supplier import Supplier, SupplierCreate, SupplierUpdate, SupplierStatus
from src.exceptions import SupplierNotFoundError

logger = logging.getLogger(__name__)


def get_suppliers(
    db: Session,
    status_filter: Optional[SupplierStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Supplier]:
    query = db.query(Supplier)
    if status_filter is not None:
        query = query.filter(Supplier.status == status_filter)
    return query.order_by(Supplier.name).offset(skip).limit(limit).all()


def get_supplier_by_id(db: Session, supplier_id: int) -> Optional[Supplier]:
    return db.get(Supplier, supplier_id)


def create_supplier(db: Session, data: SupplierCreate) -> Supplier:
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    try:
        db.commit()
        db.refresh(supplier)
    except Exception:
        db.rollback()
        raise
    return supplier


def update_supplier(db: Session, supplier_id: int, data: SupplierUpdate) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise SupplierNotFoundError(supplier_id)

    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(supplier, key, value)
    supplier.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(supplier)
    except Exception:
        db.rollback()
        raise
    return supplier


def delete_supplier(db: Session, supplier_id: int) -> None:
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise SupplierNotFoundError(supplier_id)
    db.delete(supplier)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
