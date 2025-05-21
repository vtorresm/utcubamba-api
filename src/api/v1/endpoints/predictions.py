from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import Query, Path

# Import your services and models here
from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User, Role

router = APIRouter()

# Simplified response models
class PredictionResponse(BaseModel):
    medication_id: int
    prediction: str
    probability: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EvaluationResponse(BaseModel):
    model_type: str
    metrics: Dict[str, float]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Simple test endpoint
@router.get("/test")
async def test_endpoint():
    return {"message": "Predictions endpoint is working!"}

# Predict endpoint
@router.get(
    "/predict/",
    response_model=PredictionResponse,
    tags=["predictions"],
    summary="Predecir desabastecimiento",
    description="Obtiene una predicción de desabastecimiento para un medicamento específico.",
    responses={
        200: {"description": "Predicción generada exitosamente"},
        400: {"description": "ID de medicamento no proporcionado"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        404: {"description": "Medicamento no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)
async def predict_shortage(
    medicamento_id: int = Query(..., description="ID del medicamento", gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PredictionResponse:
    try:
        # Verificar si el medicamento existe
        from src.models.medication import Medication
        medication = db.query(Medication).filter(Medication.id == medicamento_id).first()
        
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el medicamento con ID {medicamento_id}"
            )
        
        # Aquí iría la lógica real de predicción
        # Por ahora, devolvemos una respuesta de prueba
        return PredictionResponse(
            medication_id=medicamento_id,
            prediction="Sí" if medication.stock < medication.min_stock * 1.5 else "No",
            probability=0.85 if medication.stock < medication.min_stock * 1.5 else 0.15
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en la predicción: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la predicción: {str(e)}"
        )

# Metrics response model
class MetricsHistoryResponse(BaseModel):
    model_type: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metrics_history: List[Dict[str, Any]]

# Metrics endpoint
@router.get(
    "/metrics",
    response_model=MetricsHistoryResponse,
    tags=["predictions"],
    summary="Obtener métricas del modelo",
    description="Obtiene las últimas métricas de rendimiento del modelo (solo administradores).",
    responses={
        200: {"description": "Métricas obtenidas exitosamente"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        403: {"description": "No tiene permisos suficientes"},
        500: {"description": "Error interno del servidor"}
    }
)
async def get_model_metrics(
    days: int = Query(30, description="Número de días hacia atrás para obtener métricas", ge=1, le=365),
    limit: int = Query(100, description="Número máximo de registros a devolver", ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MetricsHistoryResponse:
    # Verificar si el usuario es administrador
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos suficientes para ver las métricas del modelo"
        )
    
    try:
        # Aquí iría la lógica real para obtener las métricas históricas de la base de datos
        # Por ahora, devolvemos datos de ejemplo
        from datetime import timedelta
        import random
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generar datos de ejemplo para el rango de fechas
        metrics_history = []
        current_date = start_date
        
        while current_date <= end_date and len(metrics_history) < limit:
            base_accuracy = 0.9 + random.uniform(-0.05, 0.05)  # Valor base con pequeña variación
            
            metrics_history.append({
                "date": current_date.date().isoformat(),
                "accuracy": round(base_accuracy, 4),
                "precision": round(base_accuracy - 0.01, 4),
                "recall": round(base_accuracy + 0.01, 4),
                "f1_score": round(base_accuracy, 4),
                "roc_auc": round(min(base_accuracy + 0.03, 0.99), 4)  # ROC AUC suele ser un poco más alto
            })
            
            # Mover al siguiente día
            current_date += timedelta(days=1)
        
        return MetricsHistoryResponse(
            model_type="RandomForest",
            metrics_history=metrics_history
        )
        
    except Exception as e:
        print(f"Error al obtener métricas del modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las métricas del modelo: {str(e)}"
        )

# Evaluate endpoint
@router.get(
    "/evaluate/",
    response_model=EvaluationResponse,
    tags=["predictions"],
    summary="Evaluar modelo de predicción",
    description="Evalúa el rendimiento del modelo de predicción (solo administradores).",
    responses={
        200: {"description": "Evaluación generada exitosamente"},
        400: {"description": "ID de medicamento no proporcionado"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        403: {"description": "No tiene permisos suficientes"},
        404: {"description": "Medicamento no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)
async def evaluate_model(
    medicamento_id: int = Query(..., description="ID del medicamento", gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EvaluationResponse:
    # Verificar si el usuario es administrador
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos suficientes para realizar esta acción"
        )
    
    try:
        # Verificar si el medicamento existe
        from src.models.medication import Medication
        medication = db.query(Medication).filter(Medication.id == medicamento_id).first()
        
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el medicamento con ID {medicamento_id}"
            )
        
        # Aquí iría la lógica real de evaluación del modelo
        # Por ahora, devolvemos una respuesta de prueba
        return EvaluationResponse(
            model_type="RandomForest",
            metrics={
                "accuracy": 0.95,
                "precision": 0.94,
                "recall": 0.96,
                "f1_score": 0.95,
                "roc_auc": 0.98
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en la evaluación del modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al evaluar el modelo: {str(e)}"
        )