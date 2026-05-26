from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User
from src.schemas.notification import NotificationResponse, UnreadCountResponse
from src.services import notification_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[NotificationResponse],
    summary="Listar notificaciones del usuario",
    description="Obtiene la lista de notificaciones del usuario autenticado."
)
def get_notifications(
    unread_only: bool = Query(False, description="Filtrar solo no leídas"),
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return notification_service.get_user_notifications(
        db=db, user_id=current_user.id, unread_only=unread_only, skip=skip, limit=limit
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Contar notificaciones no leídas",
    description="Obtiene la cantidad de notificaciones no leídas del usuario."
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = notification_service.get_unread_count(db=db, user_id=current_user.id)
    return UnreadCountResponse(count=count)


@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Marcar notificación como leída",
    description="Marca una notificación específica como leída."
)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = notification_service.mark_as_read(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    return notification


@router.put(
    "/read-all",
    summary="Marcar todas como leídas",
    description="Marca todas las notificaciones del usuario como leídas."
)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = notification_service.mark_all_as_read(db=db, user_id=current_user.id)
    return {"message": f"{count} notificaciones marcadas como leídas", "count": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar notificación",
    description="Elimina una notificación específica."
)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = notification_service.delete_notification(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    return None
