from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User, Role
from src.models.order import OrderStatus
from src.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderStatusUpdate
from src.services import order_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="Listar órdenes",
    description="Obtiene la lista de órdenes de pedido."
)
def get_orders(
    medication_id: Optional[int] = Query(None, description="Filtrar por medicamento"),
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filtrar por estado"),
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.get_orders(
        db=db, medication_id=medication_id,
        status_filter=status_filter, skip=skip, limit=limit
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Obtener orden por ID",
    description="Obtiene los detalles de una orden específica."
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = order_service.get_order_by_id(db=db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden con ID {order_id} no encontrada"
        )
    return order


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear orden de pedido",
    description="Crea una nueva orden de pedido para reabastecer un medicamento."
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear órdenes"
        )
    return order_service.create_order(db=db, order_data=order_data, user=current_user)


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Actualizar orden",
    description="Actualiza los datos de una orden existente."
)
def update_order(
    order_id: int,
    update_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para modificar órdenes"
        )
    order = order_service.update_order(db=db, order_id=order_id, update_data=update_data)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden con ID {order_id} no encontrada"
        )
    return order


@router.put(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Actualizar estado de orden",
    description="Actualiza el estado de una orden (ej: received incrementa el stock)."
)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para modificar órdenes"
        )
    order = order_service.update_order_status(
        db=db, order_id=order_id,
        new_status=status_update.status,
        received_date=status_update.received_date
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden con ID {order_id} no encontrada"
        )
    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar orden",
    description="Elimina una orden del sistema (solo admin)."
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar órdenes"
        )
    deleted = order_service.delete_order(db=db, order_id=order_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden con ID {order_id} no encontrada"
        )
    return None


@router.get(
    "/medication/{medication_id}",
    response_model=List[OrderResponse],
    summary="Órdenes por medicamento",
    description="Obtiene las órdenes asociadas a un medicamento específico."
)
def get_orders_by_medication(
    medication_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.get_orders_by_medication(
        db=db, medication_id=medication_id, skip=skip, limit=limit
    )
