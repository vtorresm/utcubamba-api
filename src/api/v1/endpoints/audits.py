from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User, Role
from src.models.audit import (
    Audit, AuditCreate, AuditUpdate, AuditInDB, AuditStatus
)
from src.services import audit_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[AuditInDB],
    summary="Listar auditorías",
    description="Obtiene la lista de auditorías registradas.",
)
def get_audits(
    status_filter: Optional[AuditStatus] = Query(None, alias="status", description="Filtrar por estado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return audit_service.get_audits(db=db, status_filter=status_filter, skip=skip, limit=limit)


@router.get(
    "/{audit_id}",
    response_model=AuditInDB,
    summary="Obtener auditoría por ID",
)
def get_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    audit = audit_service.get_audit_by_id(db=db, audit_id=audit_id)
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Auditoría con ID {audit_id} no encontrada")
    return audit


@router.post(
    "/",
    response_model=AuditInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar auditoría",
)
def create_audit(
    data: AuditCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para registrar auditorías")
    return audit_service.create_audit(db=db, data=data, user=current_user)


@router.put(
    "/{audit_id}",
    response_model=AuditInDB,
    summary="Actualizar auditoría",
)
def update_audit(
    audit_id: int,
    data: AuditUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [Role.ADMIN, Role.FARMACIA]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para modificar auditorías")
    return audit_service.update_audit(db=db, audit_id=audit_id, data=data)


@router.delete(
    "/{audit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar auditoría",
)
def delete_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para eliminar auditorías")
    audit_service.delete_audit(db=db, audit_id=audit_id)
    return None
