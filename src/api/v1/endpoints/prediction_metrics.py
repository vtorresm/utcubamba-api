from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User, Role
from src.models.prediction import (
    PredictionMetrics,
    PredictionMetricsCreate,
    PredictionMetricsUpdate,
    PredictionMetricsResponse
)

router = APIRouter(prefix="/prediction-metrics", tags=["prediction-metrics"])

@router.get(
    "/",
    response_model=List[PredictionMetricsResponse],
    summary="Obtener métricas de modelos de predicción",
    description="Obtiene un listado de métricas de modelos de predicción con filtros opcionales."
)
async def get_prediction_metrics(
    medication_id: Optional[int] = Query(None, description="Filtrar por ID de medicamento"),
    model_version: Optional[str] = Query(None, description="Filtrar por versión del modelo"),
    days: int = Query(30, description="Número de días hacia atrás para obtener métricas", ge=1, le=365),
    limit: int = Query(100, description="Número máximo de registros a devolver", ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[PredictionMetricsResponse]:
    """
    Obtiene métricas de modelos de predicción con filtros opcionales.
    
    Requiere autenticación y permisos de administrador.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a estas métricas"
        )
    
    query = db.query(PredictionMetrics)
    
    # Aplicar filtros
    if medication_id is not None:
        query = query.filter(PredictionMetrics.medication_id == medication_id)
    if model_version:
        query = query.filter(PredictionMetrics.model_version == model_version)
    
    # Filtrar por fecha
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(PredictionMetrics.trained_at >= start_date)
    
    # Ordenar y limitar resultados
    metrics = query.order_by(PredictionMetrics.trained_at.desc()).limit(limit).all()
    
    return metrics

@router.get(
    "/{metrics_id}",
    response_model=PredictionMetricsResponse,
    summary="Obtener métricas por ID",
    responses={
        200: {"description": "Métricas encontradas"},
        404: {"description": "Métricas no encontradas"},
        403: {"description": "No autorizado"}
    }
)
async def get_prediction_metric_by_id(
    metrics_id: int = Path(..., description="ID de las métricas"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PredictionMetricsResponse:
    """
    Obtiene métricas de un modelo de predicción por su ID.
    
    Requiere autenticación y permisos de administrador.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a estas métricas"
        )
    
    metrics = db.get(PredictionMetrics, metrics_id)
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron métricas con el ID {metrics_id}"
        )
    
    return metrics

@router.post(
    "/",
    response_model=PredictionMetricsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevas métricas de modelo",
    responses={
        201: {"description": "Métricas creadas exitosamente"},
        400: {"description": "Datos inválidos"},
        403: {"description": "No autorizado"}
    }
)
async def create_prediction_metrics(
    metrics_data: PredictionMetricsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PredictionMetricsResponse:
    """
    Registra nuevas métricas para un modelo de predicción.
    
    Requiere autenticación y permisos de administrador.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para registrar métricas"
        )
    
    # Verificar si ya existe una métrica con la misma versión para este medicamento
    existing_metrics = db.query(PredictionMetrics).filter(
        PredictionMetrics.model_version == metrics_data.model_version,
        PredictionMetrics.medication_id == metrics_data.medication_id
    ).first()
    
    if existing_metrics:
        # Actualizar métricas existentes
        for key, value in metrics_data.dict(exclude_unset=True).items():
            setattr(existing_metrics, key, value)
        existing_metrics.updated_at = datetime.utcnow()
    else:
        # Crear nuevas métricas
        metrics_dict = metrics_data.dict()
        metrics = PredictionMetrics(**metrics_dict)
        db.add(metrics)
    
    db.commit()
    db.refresh(existing_metrics if existing_metrics else metrics)
    
    return existing_metrics if existing_metrics else metrics

@router.get(
    "/medication/{medication_id}",
    response_model=List[PredictionMetricsResponse],
    summary="Obtener métricas por medicamento",
    responses={
        200: {"description": "Métricas encontradas"},
        403: {"description": "No autorizado"},
        404: {"description": "Medicamento no encontrado"}
    }
)
async def get_metrics_by_medication(
    medication_id: int = Path(..., description="ID del medicamento"),
    limit: int = Query(10, description="Número máximo de registros a devolver", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[PredictionMetricsResponse]:
    """
    Obtiene las métricas de modelos de predicción para un medicamento específico.
    
    Requiere autenticación.
    """
    # Verificar que el medicamento existe
    from src.models.medication import Medication
    medication = db.get(Medication, medication_id)
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el medicamento con ID {medication_id}"
        )
    
    # Obtener métricas ordenadas por fecha de entrenamiento (más recientes primero)
    metrics = db.query(PredictionMetrics).filter(
        PredictionMetrics.medication_id == medication_id
    ).order_by(PredictionMetrics.trained_at.desc()).limit(limit).all()
    
    return metrics

@router.get(
    "/latest/medication/{medication_id}",
    response_model=PredictionMetricsResponse,
    summary="Obtener las últimas métricas para un medicamento",
    responses={
        200: {"description": "Métricas encontradas"},
        403: {"description": "No autorizado"},
        404: {"description": "No se encontraron métricas para este medicamento"}
    }
)
async def get_latest_metrics_for_medication(
    medication_id: int = Path(..., description="ID del medicamento"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PredictionMetricsResponse:
    """
    Obtiene las métricas más recientes para un medicamento específico.
    
    Requiere autenticación.
    """
    # Verificar que el medicamento existe
    from src.models.medication import Medication
    medication = db.get(Medication, medication_id)
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el medicamento con ID {medication_id}"
        )
    
    # Obtener la métrica más reciente para este medicamento
    metrics = db.query(PredictionMetrics).filter(
        PredictionMetrics.medication_id == medication_id
    ).order_by(PredictionMetrics.trained_at.desc()).first()
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron métricas para el medicamento con ID {medication_id}"
        )
    
    return metrics
