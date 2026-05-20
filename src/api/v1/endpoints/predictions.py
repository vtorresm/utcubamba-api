from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, conint, confloat
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Tuple
import logging

# Database and authentication
from src.core.database import get_db
from src.dependencies.auth import get_current_user

# Models
from src.models.user import User, Role
from src.models.medication import Medication
from src.models.prediction import (
    Prediction, AlertLevel, PredictionItemResponse, 
    PredictionsListResponse, PredictionResponse, PredictionMetrics
)

# Services
from src.services.prediction_service import (
    predict_shortage_risk,
    get_predictions as get_predictions_service,
    calculate_risk_level,
    calculate_days_until_shortage
)

# SQLAlchemy
from sqlalchemy import func, and_, or_, text
from sqlalchemy.sql import extract, case, select

router = APIRouter()

# Simplified response models
class EvaluationResponse(BaseModel):
    model_type: str
    metrics: Dict[str, float]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskLevelCount(BaseModel):
    level: RiskLevel
    count: int
    percentage: float

class RiskLevelsResponse(BaseModel):
    total: int
    levels: List[RiskLevelCount]
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SeasonalityMetrics(BaseModel):
    medication_id: int
    medication_name: str
    seasonality_coefficient: float
    period: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class DemandTrend(BaseModel):
    period: str
    trend: Literal["up", "down", "stable"]
    confidence: float
    change_percentage: float

class HistoricalUsageItem(BaseModel):
    id: int
    date: datetime
    real_usage: float
    predicted_usage: float
    stock: Optional[float] = None

class HistoricalUsageResponse(BaseModel):
    medication_id: int
    month: int
    year: int
    real_usage_total: float
    predicted_usage_total: float
    records: int
    items: List[HistoricalUsageItem]


# Simple test endpoint
@router.get(
    "/test",
    tags=["predictions"],
    summary="Endpoint de prueba",
    description="""
    Endpoint de prueba para verificar que el módulo de predicciones está funcionando correctamente.

    No requiere autenticación y siempre devuelve un mensaje de éxito.
    """,
    response_description="Mensaje de confirmación de que el endpoint está funcionando",
    responses={
        200: {
            "description": "El endpoint está funcionando correctamente",
            "content": {
                "application/json": {
                    "example": {"message": "Predictions endpoint is working!"}
                }
            }
        }
    }
)
async def test_endpoint():
    """
    Verifica que el endpoint de predicciones esté funcionando.

    Returns:
        dict: Un mensaje indicando que el endpoint está funcionando correctamente.
    """
    return {"message": "Predictions endpoint is working!"}

@router.get(
    "/",
    response_model=PredictionsListResponse,
    tags=["predictions"],
    summary="Obtener todas las predicciones",
    description="""
    Recupera una lista paginada de todas las predicciones de desabastecimiento.
    Permite filtrar por ID de medicamento y paginar los resultados.
    """,
    responses={
        200: {"description": "Lista de predicciones recuperada exitosamente"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        500: {"description": "Error interno del servidor"}
    }
)
async def get_all_predictions(
    medication_id: Optional[int] = Query(None, description="Filtrar por ID de medicamento"),
    skip: int = Query(0, ge=0, description="Número de elementos a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de elementos a devolver"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PredictionsListResponse:
    try:
        query = db.query(Prediction)
        if medication_id:
            query = query.filter(Prediction.medication_id == medication_id)

        total_predictions = query.count()
        predictions = query.offset(skip).limit(limit).all()

        return PredictionsListResponse(
            total=total_predictions,
            predictions=[
                PredictionResponse(
                    medication_id=p.medication_id,
                    prediction="shortage" if p.shortage else "no_shortage",
                    probability=p.probability if p.probability is not None else 0.0,
                    timestamp=p.date
                ) for p in predictions
            ]
        )
    except Exception as e:
        print(f"Error al obtener todas las predicciones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener predicciones: {str(e)}"
        )

# Predict endpoint
@router.get(
    "/predict/",
    response_model=PredictionResponse,
    tags=["predictions"],
    summary="Predecir riesgo de desabastecimiento",
    description="""
    Obtiene una predicción de riesgo de desabastecimiento para un medicamento específico.
    
    Este endpoint utiliza un modelo de Random Forest entrenado con el historial de consumo
    del medicamento, patrones estacionales y tendencias para predecir posibles
    desabastecimientos en el corto y mediano plazo.
    
    El modelo considera:
    - Historial de movimientos de inventario
    - Estacionalidad (patrones mensuales, semanales)
    - Tendencias de consumo
    - Niveles de stock actuales
    - Tiempos de reposición
    
    Requiere autenticación con token JWT.
    """,
    response_description="Predicción de riesgo de desabastecimiento generada exitosamente",
    responses={
        200: {
            "description": "Predicción generada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 101,
                        "medication_id": 1,
                        "date": "2025-07-06T17:18:18.123456",
                        "real_usage": 0.0,
                        "predicted_usage": 25.5,
                        "stock": 150,
                        "month_of_year": 7,
                        "regional_demand": 0.0,
                        "shortage": False,
                        "probability": 0.15,
                        "confidence_interval_lower": 18.2,
                        "confidence_interval_upper": 32.8,
                        "alert_level": "low",
                        "trend": "stable",
                        "seasonality_coefficient": 0.9,
                        "created_at": "2025-07-06T17:18:18.123456",
                        "updated_at": "2025-07-06T17:18:18.123456"
                    }
                }
            }
        },
        400: {
            "description": "Solicitud incorrecta",
            "content": {
                "application/json": {
                    "example": {"detail": "ID de medicamento no válido"}
                }
            }
        },
        401: {
            "description": "No autorizado",
            "content": {
                "application/json": {
                    "example": {"detail": "No autenticado"}
                }
            }
        },
        404: {
            "description": "Recurso no encontrado",
            "content": {
                "application/json": {
                    "example": {"detail": "Medicamento no encontrado"}
                }
            }
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {"detail": "Error al procesar la predicción"}
                }
            }
        }
    }
)
async def predict_shortage(
    medicamento_id: int = Query(..., description="ID del medicamento", gt=0),
    dias_prediccion: int = Query(30, description="Días a futuro para la predicción", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PredictionResponse:
    """
    Predice el riesgo de desabastecimiento para un medicamento específico.
    
    Args:
        medicamento_id: ID del medicamento para el cual se realizará la predicción
        dias_prediccion: Número de días en el futuro para la predicción (1-90)
        
    Returns:
        PredictionResponse: Objeto con la predicción y métricas asociadas
    """
    try:
        logger.info(f"Iniciando predicción para medicamento ID: {medicamento_id}")
        
        # Verificar si el medicamento existe
        medication = db.query(Medication).filter(Medication.id == medicamento_id).first()
        if not medication:
            logger.warning(f"Medicamento no encontrado: ID {medicamento_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el medicamento con ID {medicamento_id}"
            )
            
        # Obtener predicción del servicio
        prediction_result = predict_shortage_risk(
            db=db,
            medication_id=medicamento_id,
            days_ahead=dias_prediccion
        )
        
        # Calcular intervalo de confianza (aproximado basado en el error del modelo)
        mae = prediction_result.get('metrics', {}).get('mae', 0)
        predicted_usage = prediction_result.get('predicted_usage', 0)
        
        # Crear respuesta
        response_data = {
            "id": 0,  # Se actualizará después de guardar
            "medication_id": medicamento_id,
            "date": datetime.utcnow(),
            "real_usage": 0.0,  # Se actualizará cuando haya datos reales
            "predicted_usage": predicted_usage,
            "stock": prediction_result.get('current_stock', 0),
            "month_of_year": datetime.utcnow().month,
            "regional_demand": 0.0,  # Se podría obtener de datos externos
            "shortage": prediction_result.get('days_until_shortage', 999) <= 7,
            "probability": prediction_result.get('confidence', 0.5),
            "confidence_interval_lower": max(0, predicted_usage - mae),
            "confidence_interval_upper": predicted_usage + mae,
            "alert_level": prediction_result.get('risk_level', 'low'),
            "trend": 'up' if prediction_result.get('predicted_usage', 0) > 0 else 'down',
            "seasonality_coefficient": 1.0,  # Se podría calcular basado en estacionalidad
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Guardar predicción en la base de datos
        db_prediction = Prediction(**response_data)
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        # Actualizar ID en la respuesta
        response_data["id"] = db_prediction.id
        
        logger.info(f"Predicción completada para medicamento ID: {medicamento_id}")
        return PredictionResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en la predicción para medicamento {medicamento_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la predicción: {str(e)}"
        )

# Metrics response model
class MetricsHistoryResponse(BaseModel):
    model_type: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metrics_history: List[Dict[str, Any]]

@router.get(
    "/metrics/",
    response_model=MetricsHistoryResponse,
    tags=["predictions"],
    summary="Obtener métricas del modelo de predicción",
    description="""
    Obtiene métricas históricas del rendimiento del modelo de predicción.
    
    Incluye métricas como precisión, recall, F1-score, MAE, MSE y R².
    """,
    response_description="Métricas del modelo de predicción",
    responses={
        200: {
            "description": "Métricas obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "model_type": "RandomForestRegressor",
                        "last_updated": "2025-07-06T17:30:00.000000",
                        "metrics_history": [
                            {
                                "date": "2025-07-05T10:00:00.000000",
                                "mae": 5.2,
                                "mse": 42.3,
                                "r2": 0.85,
                                "samples": 150
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Error al obtener las métricas del modelo"
        }
    }
)
async def get_model_metrics(
    days: int = Query(30, description="Número de días hacia atrás para obtener métricas", ge=1, le=365),
    limit: int = Query(100, description="Número máximo de registros a devolver", ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MetricsHistoryResponse:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos suficientes para ver las métricas del modelo"
        )

    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        metrics_query = (
            db.query(PredictionMetrics)
            .filter(PredictionMetrics.created_at >= start_date)
            .order_by(PredictionMetrics.created_at.desc())
            .limit(limit)
        )

        metrics_history = [
            {
                "date": m.created_at,
                "mae": m.mae,
                "mse": m.mse,
                "r2": m.r2_score,
            }
            for m in metrics_query.all()
        ]

        return MetricsHistoryResponse(
            model_type="RandomForestRegressor",
            last_updated=datetime.utcnow(),
            metrics_history=metrics_history
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener métricas del modelo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener las métricas del modelo"
        )

@router.get(
    "/history/",
    response_model=List[PredictionResponse],
    tags=["predictions"],
    summary="Obtener historial de predicciones",
    description="""
    Obtiene el historial de predicciones para uno o todos los medicamentos.
    
    Permite filtrar por rango de fechas, ID de medicamento y paginar los resultados.
    """,
    response_description="Lista de predicciones históricas",
    responses={
        200: {
            "description": "Historial de predicciones obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 101,
                            "medication_id": 1,
                            "date": "2025-07-01T10:30:00.000000",
                            "real_usage": 23.5,
                            "predicted_usage": 25.2,
                            "stock": 150,
                            "month_of_year": 7,
                            "shortage": False,
                            "probability": 0.15,
                            "alert_level": "low"
                        }
                    ]
                }
            }
        },
        400: {
            "description": "Parámetros de consulta inválidos"
        },
        401: {
            "description": "No autorizado"
        },
        500: {
            "description": "Error al obtener el historial de predicciones"
        }
    }
)
async def get_prediction_history(
    medication_id: Optional[int] = Query(None, description="Filtrar por ID de medicamento"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    limit: int = Query(100, description="Número máximo de resultados", ge=1, le=1000),
    offset: int = Query(0, description="Desplazamiento para paginación", ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[PredictionResponse]:
    """
    Obtiene el historial de predicciones con filtros opcionales.
    
    Args:
        medication_id: Filtrar por ID de medicamento específico
        start_date: Filtrar predicciones desde esta fecha
        end_date: Filtrar predicciones hasta esta fecha
        limit: Número máximo de resultados por página (1-1000)
        offset: Desplazamiento para paginación
        
    Returns:
        List[PredictionResponse]: Lista de predicciones que coinciden con los filtros
    """
    try:
        # Construir consulta base
        query = db.query(Prediction)
        
        # Aplicar filtros
        if medication_id is not None:
            query = query.filter(Prediction.medication_id == medication_id)
            
        if start_date is not None:
            query = query.filter(Prediction.date >= start_date)
            
        if end_date is not None:
            # Asegurarse de incluir todo el día de la fecha final
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Prediction.date <= end_date)
        
        # Ordenar por fecha descendente (más recientes primero)
        query = query.order_by(Prediction.date.desc())
        
        # Aplicar paginación
        predictions = query.offset(offset).limit(limit).all()
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error al obtener historial de predicciones: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al recuperar el historial de predicciones"
        )


@router.get(
    "/seasonality",
    response_model=List[SeasonalityMetrics],
    tags=["predictions"],
    summary="Obtener métricas de estacionalidad",
    description="""
    Obtiene métricas de estacionalidad para los medicamentos.
    Incluye coeficiente de estacionalidad y período de análisis.
    """,
    responses={
        200: {"description": "Métricas de estacionalidad obtenidas exitosamente"},
        400: {"description": "Parámetros inválidos"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        500: {"description": "Error interno del servidor"}
    }
)
async def get_seasonality_metrics(
    min_coefficient: float = Query(0.1, description="Coeficiente mínimo de estacionalidad a incluir", ge=0, le=1),
    limit: int = Query(100, description="Número máximo de resultados a devolver", ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[SeasonalityMetrics]:
    """
    Obtiene métricas de estacionalidad para los medicamentos con predicciones recientes.

    Args:
        min_coefficient: Filtra medicamentos con coeficiente de estacionalidad mayor o igual
        limit: Límite de resultados a devolver

    Returns:
        Lista de métricas de estacionalidad por medicamento
    """
    try:
        # Obtener medicamentos con predicciones recientes (últimos 12 meses)
        one_year_ago = datetime.utcnow() - timedelta(days=365)

        # Consulta para obtener medicamentos con predicciones recientes
        recent_meds_subq = db.query(
            Prediction.medication_id
        ).filter(
            Prediction.date >= one_year_ago
        ).group_by(
            Prediction.medication_id
        ).subquery()

        # Obtener medicamentos con predicciones recientes
        meds_with_predictions = db.query(Medication).join(
            recent_meds_subq,
            Medication.id == recent_meds_subq.c.medication_id
        ).limit(limit).all()

        results = []
        for med in meds_with_predictions:
            # Obtener predicciones mensuales para el último año
            monthly_data = db.query(
                extract('month', Prediction.date).label('month'),
                func.avg(Prediction.predicted_usage).label('avg_usage')
            ).filter(
                Prediction.medication_id == med.id,
                Prediction.date >= one_year_ago
            ).group_by(
                extract('month', Prediction.date)
            ).all()

            if len(monthly_data) < 3:  # Mínimo 3 meses de datos
                continue

            # Calcular el coeficiente de estacionalidad
            # (En una implementación real, usaríamos un método más sofisticado)
            usages = [data.avg_usage for data in monthly_data]
            avg_usage = sum(usages) / len(usages)
            if avg_usage == 0:
                continue

            # Calcular la desviación estándar relativa como aproximación simple
            # de la estacionalidad
            variance = sum((x - avg_usage) ** 2 for x in usages) / len(usages)
            std_dev = variance ** 0.5
            coefficient = std_dev / avg_usage if avg_usage > 0 else 0

            # Solo incluir si supera el umbral mínimo
            if coefficient >= min_coefficient:
                results.append(SeasonalityMetrics(
                    medication_id=med.id,
                    medication_name=med.name,
                    seasonality_coefficient=round(coefficient, 4),
                    period='monthly'
                ))

        # Ordenar por coeficiente de estacionalidad descendente
        results.sort(key=lambda x: x.seasonality_coefficient, reverse=True)

        return results

    except Exception as e:
        print(f"Error al obtener métricas de estacionalidad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener métricas de estacionalidad: {str(e)}"
        )

@router.get(
    "/demand-trend",
    response_model=DemandTrend,
    tags=["predictions"],
    summary="Analizar tendencia de la demanda",
    description="""
    Analiza la tendencia general de la demanda de medicamentos en el sistema.
    Proporciona información sobre si la demanda está aumentando, disminuyendo o estable.
    """,
    responses={
        200: {"description": "Análisis de tendencia de demanda exitoso"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        500: {"description": "Error interno del servidor"}
    }
)
async def get_demand_trend(
    period: str = Query("month", description="Período de análisis", regex="^(day|week|month|quarter|year)$"),
    lookback: int = Query(6, description="Número de períodos a analizar hacia atrás", ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DemandTrend:
    """
    Analiza la tendencia de la demanda de medicamentos en el tiempo.

    Args:
        period: Unidad de tiempo para el análisis (day, week, month, quarter, year)
        lookback: Número de períodos a analizar hacia atrás

    Returns:
        Objeto DemandTrend con la tendencia, confianza y porcentaje de cambio
    """
    try:
        # Mapear el período a una función de extracción de fecha
        period_map = {
            'day': extract('day', Prediction.date),
            'week': extract('week', Prediction.date),
            'month': extract('month', Prediction.date),
            'quarter': func.date_trunc('quarter', Prediction.date),
            'year': extract('year', Prediction.date)
        }

        period_expr = period_map.get(period, extract('month', Prediction.date))

        # Obtener datos agregados por período
        trend_data = db.query(
            period_expr.label('period'),
            func.sum(Prediction.predicted_usage).label('total_usage'),
            func.count(Prediction.id).label('prediction_count')
        ).group_by(
            period_expr
        ).order_by(
            period_expr.desc()
        ).limit(lookback).all()

        if len(trend_data) < 2:
            return DemandTrend(
                period=period,
                trend="stable",
                confidence=0.0,
                change_percentage=0.0
            )

        # Ordenar los datos cronológicamente
        trend_data_sorted = sorted(trend_data, key=lambda x: x.period)

        # Calcular la tendencia usando regresión lineal simple
        periods = list(range(len(trend_data_sorted)))
        usages = [float(data.total_usage) for data in trend_data_sorted]

        # Calcular la pendiente (tendencia)
        n = len(periods)
        sum_x = sum(periods)
        sum_y = sum(usages)
        sum_xy = sum(x * y for x, y in zip(periods, usages))
        sum_x2 = sum(x * x for x in periods)

        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

            # Calcular el coeficiente de correlación (R) como medida de confianza
            mean_y = sum_y / n
            ss_total = sum((y - mean_y) ** 2 for y in usages)
            ss_res = sum((y - (slope * x + (sum_y/n - slope * sum_x/n))) ** 2
                        for x, y in zip(periods, usages))

            if ss_total == 0:
                r_squared = 0
            else:
                r_squared = 1 - (ss_res / ss_total)

            # Determinar la dirección de la tendencia
            if abs(slope) < 0.001:  # Umbral para considerar estable
                trend = "stable"
            else:
                trend = "up" if slope > 0 else "down"

            # Calcular el cambio porcentual del primer al último período
            first_usage = usages[0]
            last_usage = usages[-1]

            if first_usage == 0:
                change_pct = 0.0
            else:
                change_pct = ((last_usage - first_usage) / abs(first_usage)) * 100

            return DemandTrend(
                period=period,
                trend=trend,
                confidence=min(max(abs(r_squared), 0.0), 1.0),  # Asegurar entre 0 y 1
                change_percentage=round(change_pct, 2)
            )

        except ZeroDivisionError:
            # En caso de división por cero, devolver tendencia estable
            return DemandTrend(
                period=period,
                trend="stable",
                confidence=0.0,
                change_percentage=0.0
            )

    except Exception as e:
        print(f"Error al analizar tendencia de demanda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al analizar tendencia de demanda: {str(e)}"
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

@router.get(
    "/uso-historico/",
    response_model=HistoricalUsageResponse,
    tags=["predictions"],
    summary="Obtener uso histórico de un medicamento por mes y año",
    description="""
    Devuelve el uso real y predicho de un medicamento para un mes y año específicos, incluyendo el detalle de cada registro.
    """,
    responses={
        200: {"description": "Uso histórico obtenido exitosamente"},
        400: {"description": "Parámetros inválidos"},
        404: {"description": "No hay datos para ese medicamento/mes/año"},
        401: {"description": "No autorizado"},
    }
)
async def get_historical_usage(
    medicamento_id: int = Query(..., description="ID del medicamento", gt=0),
    mes: int = Query(..., description="Mes (1-12)", ge=1, le=12),
    anio: int = Query(..., description="Año (ej: 2024)", ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> HistoricalUsageResponse:
    try:
        # Verificar si el medicamento existe
        medication = db.query(Medication).filter(Medication.id == medicamento_id).first()
        if not medication:
            raise HTTPException(status_code=404, detail="Medicamento no encontrado")

        # Obtener los registros individuales
        registros = db.query(Prediction).filter(
            Prediction.medication_id == medicamento_id,
            extract('month', Prediction.date) == mes,
            extract('year', Prediction.date) == anio
        ).all()

        if not registros:
            raise HTTPException(status_code=404, detail="No hay datos para ese medicamento/mes/año")

        # Resumen
        real_usage_total = sum(r.real_usage or 0 for r in registros)
        predicted_usage_total = sum(r.predicted_usage or 0 for r in registros)

        items = [
            HistoricalUsageItem(
                id=r.id,
                date=r.date,
                real_usage=r.real_usage,
                predicted_usage=r.predicted_usage,
                stock=getattr(r, "stock", None)
            )
            for r in registros
        ]

        return HistoricalUsageResponse(
            medication_id=medicamento_id,
            month=mes,
            year=anio,
            real_usage_total=real_usage_total,
            predicted_usage_total=predicted_usage_total,
            records=len(registros),
            items=items
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en uso histórico: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener uso histórico: {str(e)}")