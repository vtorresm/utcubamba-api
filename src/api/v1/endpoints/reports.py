from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User, Role
from src.models.report import ReportType
from src.schemas.report import ReportCreate, ReportResponse
from src.services import report_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[ReportResponse],
    summary="Listar reportes",
    description="Obtiene la lista de reportes generados."
)
def get_reports(
    report_type: Optional[ReportType] = Query(None, alias="type", description="Filtrar por tipo"),
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == Role.ADMIN:
        return report_service.get_reports(
            db=db, user_id=None, report_type=report_type, skip=skip, limit=limit
        )
    return report_service.get_reports(
        db=db, user_id=current_user.id, report_type=report_type, skip=skip, limit=limit
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Obtener reporte por ID",
    description="Obtiene los detalles de un reporte específico."
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = report_service.get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporte con ID {report_id} no encontrado"
        )
    if current_user.role != Role.ADMIN and report.generated_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver este reporte"
        )
    return report


@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar reporte",
    description="Genera un nuevo reporte con los parámetros especificados."
)
def create_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return report_service.generate_report(db=db, report_data=report_data, user=current_user)


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar reporte",
    description="Elimina un reporte del sistema."
)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = report_service.get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reporte con ID {report_id} no encontrado"
        )
    if current_user.role != Role.ADMIN and report.generated_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar este reporte"
        )
    report_service.delete_report(db=db, report_id=report_id)
    return None
