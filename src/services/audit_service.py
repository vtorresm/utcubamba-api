from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
import logging

from src.models.audit import Audit, AuditCreate, AuditUpdate, AuditStatus
from src.models.user import User
from src.exceptions import AuditNotFoundError

logger = logging.getLogger(__name__)


def _query_with_relations(db: Session):
    return db.query(Audit).options(joinedload(Audit.responsible))


def get_audits(
    db: Session,
    status_filter: Optional[AuditStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Audit]:
    query = _query_with_relations(db)
    if status_filter is not None:
        query = query.filter(Audit.status == status_filter)
    return query.order_by(Audit.audit_date.desc()).offset(skip).limit(limit).all()


def get_audit_by_id(db: Session, audit_id: int) -> Optional[Audit]:
    return _query_with_relations(db).filter(Audit.id == audit_id).first()


def create_audit(db: Session, data: AuditCreate, user: User) -> Audit:
    audit = Audit(
        sector=data.sector,
        documentation_score=data.documentation_score,
        precision_score=data.precision_score,
        notes=data.notes,
        responsible_id=user.id,
        status=AuditStatus.IN_PROGRESS,
        audit_date=datetime.utcnow(),
    )
    db.add(audit)
    try:
        db.commit()
        db.refresh(audit)
    except Exception:
        db.rollback()
        raise
    return get_audit_by_id(db, audit.id)


def update_audit(db: Session, audit_id: int, data: AuditUpdate) -> Audit:
    audit = db.get(Audit, audit_id)
    if not audit:
        raise AuditNotFoundError(audit_id)

    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(audit, key, value)
    audit.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(audit)
    except Exception:
        db.rollback()
        raise
    return get_audit_by_id(db, audit.id)


def delete_audit(db: Session, audit_id: int) -> None:
    audit = db.get(Audit, audit_id)
    if not audit:
        raise AuditNotFoundError(audit_id)
    db.delete(audit)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
