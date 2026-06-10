from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User, Role
from src.models.supplier import (
    Supplier, SupplierCreate, SupplierUpdate, SupplierInDB, SupplierStatus
)
from src.services import supplier_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[SupplierInDB],
    summary="Listar proveedores",
    description="Obtiene la lista de proveedores registrados.",
)
def get_suppliers(
    status_filter: Optional[SupplierStatus] = Query(None, alias="status", description="Filtrar por estado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return supplier_service.get_suppliers(db=db, status_filter=status_filter, skip=skip, limit=limit)


@router.get(
    "/{supplier_id}",
    response_model=SupplierInDB,
    summary="Obtener proveedor por ID",
)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supplier = supplier_service.get_supplier_by_id(db=db, supplier_id=supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Proveedor con ID {supplier_id} no encontrado")
    return supplier


@router.post(
    "/",
    response_model=SupplierInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proveedor",
)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para crear proveedores")
    return supplier_service.create_supplier(db=db, data=data)


@router.put(
    "/{supplier_id}",
    response_model=SupplierInDB,
    summary="Actualizar proveedor",
)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para modificar proveedores")
    return supplier_service.update_supplier(db=db, supplier_id=supplier_id, data=data)


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar proveedor",
)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para eliminar proveedores")
    supplier_service.delete_supplier(db=db, supplier_id=supplier_id)
    return None
