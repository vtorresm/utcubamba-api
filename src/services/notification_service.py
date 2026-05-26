from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from src.models.notification import (
    Notification, NotificationCreate, NotificationType, NotificationLevel
)
from src.exceptions import NotificationNotFoundError

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    type: NotificationType = NotificationType.INFO,
    level: NotificationLevel = NotificationLevel.LOW,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
    metadata_: Optional[dict] = None
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        level=level,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        metadata_=metadata_ or {}
    )
    db.add(notification)
    try:
        db.commit()
        db.refresh(notification)
    except Exception:
        db.rollback()
        raise
    return notification


def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50
) -> List[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.read == False)
    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


def get_unread_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False
    ).count()


def mark_as_read(db: Session, notification_id: int, user_id: int) -> Notification:
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if not notification:
        raise NotificationNotFoundError(notification_id)
    notification.read = True
    try:
        db.commit()
        db.refresh(notification)
    except Exception:
        db.rollback()
        raise
    return notification


def mark_all_as_read(db: Session, user_id: int) -> int:
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False
    ).update({"read": True}, synchronize_session='fetch')
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return count


def delete_notification(db: Session, notification_id: int, user_id: int) -> None:
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if not notification:
        raise NotificationNotFoundError(notification_id)
    db.delete(notification)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def create_shortage_alert(
    db: Session,
    user_id: int,
    medication_name: str,
    medication_id: int,
    days_until_shortage: Optional[int],
    level: NotificationLevel
) -> Notification:
    if days_until_shortage is not None and days_until_shortage <= 0:
        title = f"Desabastecimiento: {medication_name}"
        message = f"El medicamento '{medication_name}' está actualmente en desabastecimiento."
    elif days_until_shortage is not None and days_until_shortage <= 7:
        title = f"Alerta crítica: {medication_name}"
        message = f"El medicamento '{medication_name}' se agotará en aproximadamente {days_until_shortage} días."
    else:
        title = f"Alerta de stock: {medication_name}"
        message = f"El medicamento '{medication_name}' tiene un riesgo de desabastecimiento."
        level = NotificationLevel.LOW

    return create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        type=NotificationType.SHORTAGE_ALERT,
        level=level,
        related_entity_type="medication",
        related_entity_id=medication_id
    )
