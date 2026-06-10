from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
import logging

from src.models.lot import Lot, LotCreate, LotUpdate, LotStatus, LotEvent, LotEventCreate
from src.models.medication import Medication
from src.exceptions import LotNotFoundError, MedicationNotFoundError

logger = logging.getLogger(__name__)


def _query_with_relations(db: Session):
    return db.query(Lot).options(joinedload(Lot.medication), joinedload(Lot.events))


def get_lots(
    db: Session,
    status_filter: Optional[LotStatus] = None,
    medication_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Lot]:
    query = _query_with_relations(db)
    if status_filter is not None:
        query = query.filter(Lot.status == status_filter)
    if medication_id is not None:
        query = query.filter(Lot.medication_id == medication_id)
    return query.order_by(Lot.created_at.desc()).offset(skip).limit(limit).unique().all()


def get_lot_by_id(db: Session, lot_id: int) -> Optional[Lot]:
    return _query_with_relations(db).filter(Lot.id == lot_id).first()


def create_lot(db: Session, data: LotCreate) -> Lot:
    medication = db.get(Medication, data.medication_id)
    if not medication:
        raise MedicationNotFoundError(data.medication_id)

    lot = Lot(**data.model_dump())
    db.add(lot)
    try:
        db.commit()
        db.refresh(lot)
    except Exception:
        db.rollback()
        raise

    # Primer evento de trazabilidad: recepción.
    event = LotEvent(
        lot_id=lot.id,
        title="Recibido en almacén",
        detail=f"Lote {lot.code} registrado en el sistema",
        event_date=datetime.utcnow(),
        completed=True,
        step_order=0,
    )
    db.add(event)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_lot_by_id(db, lot.id)


def update_lot(db: Session, lot_id: int, data: LotUpdate) -> Lot:
    lot = db.get(Lot, lot_id)
    if not lot:
        raise LotNotFoundError(lot_id)

    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(lot, key, value)
    lot.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(lot)
    except Exception:
        db.rollback()
        raise
    return get_lot_by_id(db, lot.id)


def delete_lot(db: Session, lot_id: int) -> None:
    lot = db.get(Lot, lot_id)
    if not lot:
        raise LotNotFoundError(lot_id)
    db.delete(lot)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def add_lot_event(db: Session, lot_id: int, data: LotEventCreate) -> Lot:
    lot = db.get(Lot, lot_id)
    if not lot:
        raise LotNotFoundError(lot_id)

    event = LotEvent(lot_id=lot_id, **data.model_dump())
    db.add(event)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return get_lot_by_id(db, lot_id)
