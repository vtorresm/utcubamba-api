from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User, Role
from src.models.lot import (
    Lot, LotCreate, LotUpdate, LotInDB, LotStatus, LotEventCreate
)
from src.services import lot_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[LotInDB],
    summary="Listar lotes",
    description="Obtiene la lista de lotes con su información de trazabilidad.",
)
def get_lots(
    status_filter: Optional[LotStatus] = Query(None, alias="status", description="Filtrar por estado"),
    medication_id: Optional[int] = Query(None, description="Filtrar por medicamento"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return lot_service.get_lots(db=db, status_filter=status_filter, medication_id=medication_id, skip=skip, limit=limit)


@router.get(
    "/{lot_id}",
    response_model=LotInDB,
    summary="Obtener lote por ID",
    description="Obtiene el detalle de un lote, incluyendo su línea de tiempo de trazabilidad.",
)
def get_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lot = lot_service.get_lot_by_id(db=db, lot_id=lot_id)
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lote con ID {lot_id} no encontrado")
    return lot


@router.post(
    "/",
    response_model=LotInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar lote",
)
def create_lot(
    data: LotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para registrar lotes")
    return lot_service.create_lot(db=db, data=data)


@router.put(
    "/{lot_id}",
    response_model=LotInDB,
    summary="Actualizar lote",
)
def update_lot(
    lot_id: int,
    data: LotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para modificar lotes")
    return lot_service.update_lot(db=db, lot_id=lot_id, data=data)


@router.post(
    "/{lot_id}/events",
    response_model=LotInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar evento de trazabilidad",
    description="Agrega un nuevo paso a la línea de tiempo de trazabilidad del lote.",
)
def add_lot_event(
    lot_id: int,
    data: LotEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para modificar lotes")
    return lot_service.add_lot_event(db=db, lot_id=lot_id, data=data)


@router.delete(
    "/{lot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar lote",
)
def delete_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para eliminar lotes")
    lot_service.delete_lot(db=db, lot_id=lot_id)
    return None
