from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User, Role
from src.models.delivery import (
    Delivery, DeliveryCreate, DeliveryUpdate, DeliveryInDB, DeliveryStatus
)
from src.services import delivery_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[DeliveryInDB],
    summary="Listar entregas",
    description="Obtiene la lista de entregas registradas.",
)
def get_deliveries(
    status_filter: Optional[DeliveryStatus] = Query(None, alias="status", description="Filtrar por estado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delivery_service.get_deliveries(db=db, status_filter=status_filter, skip=skip, limit=limit)


@router.get(
    "/{delivery_id}",
    response_model=DeliveryInDB,
    summary="Obtener entrega por ID",
)
def get_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delivery = delivery_service.get_delivery_by_id(db=db, delivery_id=delivery_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entrega con ID {delivery_id} no encontrada")
    return delivery


@router.post(
    "/",
    response_model=DeliveryInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar entrega",
)
def create_delivery(
    data: DeliveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para registrar entregas")
    return delivery_service.create_delivery(db=db, data=data)


@router.put(
    "/{delivery_id}",
    response_model=DeliveryInDB,
    summary="Actualizar entrega",
)
def update_delivery(
    delivery_id: int,
    data: DeliveryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para modificar entregas")
    return delivery_service.update_delivery(db=db, delivery_id=delivery_id, data=data)


@router.delete(
    "/{delivery_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar entrega",
)
def delete_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para eliminar entregas")
    delivery_service.delete_delivery(db=db, delivery_id=delivery_id)
    return None
