from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from pydantic import validator

if TYPE_CHECKING:
    from .medication import Medication
    from .movement import Movement

class AlertLevel(str, Enum):
    """Niveles de alerta para predicciones de desabastecimiento."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TrendDirection(str, Enum):
    """Dirección de la tendencia en el consumo del medicamento."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class PredictionBase(SQLModel):
    """
    Modelo base para predicciones de desabastecimiento de medicamentos.
    
    Este modelo contiene los atributos comunes para las predicciones, incluyendo métricas
    de consumo, niveles de stock, y análisis de tendencias.
    """
    date: datetime = Field(
        default_factory=datetime.utcnow, 
        nullable=False,
        description="Fecha y hora en que se realizó la predicción"
    )
    real_usage: float = Field(
        ..., 
        gt=0, 
        description="Consumo real del medicamento (R_i) en unidades"
    )
    predicted_usage: float = Field(
        ..., 
        gt=0, 
        description="Consumo predicho del medicamento (P_i) en unidades"
    )
    stock: float = Field(
        ..., 
        ge=0, 
        description="Cantidad disponible en inventario"
    )
    month_of_year: int = Field(
        ..., 
        ge=1, 
        le=12, 
        description="Mes del año (1-12) para el que se realizó la predicción"
    )
    regional_demand: float = Field(
        ..., 
        ge=0, 
        description="Demanda regional promedio para este tipo de medicamento"
    )
    restock_time: Optional[float] = Field(
        None, 
        ge=0, 
        description="Tiempo estimado de reabastecimiento en días"
    )
    shortage: bool = Field(
        False, 
        description="Indica si se predice desabastecimiento (True) o no (False)"
    )
    probability: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Probabilidad de desabastecimiento (0-1)"
    )
    
    # Análisis estacional
    seasonality_coefficient: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Fuerza de la estacionalidad (0-1), donde 1 indica estacionalidad fuerte"
    )
    trend: Optional[TrendDirection] = Field(
        None, 
        description="Dirección de la tendencia de consumo (creciente, decreciente o estable)"
    )
    
    # Sistema de alertas
    alert_level: Optional[AlertLevel] = Field(
        None, 
        description="Nivel de alerta generado por la predicción"
    )
    alert_message: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Mensaje descriptivo sobre la alerta generada"
    )
    resolved_at: Optional[datetime] = Field(
        None, 
        description="Fecha y hora en que se resolvió la alerta, si aplica"
    )
    
    # Métricas de confianza
    confidence_interval_lower: Optional[float] = Field(
        None,
        ge=0,
        description="Límite inferior del intervalo de confianza del 95% para la predicción"
    )
    confidence_interval_upper: Optional[float] = Field(
        None,
        ge=0,
        description="Límite superior del intervalo de confianza del 95% para la predicción"
    )
    
    # Metadatos
    metadata_: Optional[dict] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Metadatos adicionales sobre la predicción, como parámetros del modelo"
    )
    
    # Claves foráneas
    medication_id: int = Field(
        foreign_key="medications.id",
        description="ID del medicamento asociado a esta predicción"
    )
    movement_id: Optional[int] = Field(
        default=None, 
        foreign_key="movements.id",
        description="ID del movimiento de inventario asociado, si aplica"
    )
    prediction_metrics_id: Optional[int] = Field(
        default=None,
        foreign_key="prediction_metrics.id",
        description="""
        ID de las métricas del modelo que generó esta predicción.
        Permite rastrear el rendimiento del modelo para cada predicción.
        """
    )

class Prediction(PredictionBase, table=True):
    """Prediction model for database."""
    __tablename__ = "predictions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Relationships
    medication: "Medication" = Relationship(back_populates="predictions")
    movement: Optional["Movement"] = Relationship(back_populates="prediction")
    
    # Relación con PredictionMetrics
    prediction_metrics_id: Optional[int] = Field(
        default=None, 
        foreign_key="prediction_metrics.id",
        description="ID de las métricas del modelo que generó esta predicción"
    )
    metrics: Optional["PredictionMetrics"] = Relationship(back_populates="predictions")

class PredictionCreate(PredictionBase):
    """Model for creating a new prediction."""
    pass

class PredictionUpdate(SQLModel):
    """Model for updating an existing prediction."""
    date: Optional[datetime] = None
    real_usage: Optional[float] = None
    predicted_usage: Optional[float] = None
    stock: Optional[float] = None
    month_of_year: Optional[int] = None
    regional_demand: Optional[float] = None
    restock_time: Optional[float] = None
    shortage: Optional[bool] = None
    probability: Optional[float] = None
    medication_id: Optional[int] = None
    movement_id: Optional[int] = None

class PredictionInDB(PredictionBase):
    """Prediction model for returning prediction data."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class PredictionResponse(PredictionBase):
    """
    Modelo de respuesta para las predicciones.
    
    Incluye todos los campos de PredictionBase más los campos adicionales necesarios para la respuesta.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    prediction_metrics_id: Optional[int] = None
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        
        schema_extra = {
            "example": {
                "id": 101,
                "medication_id": 1,
                "date": "2025-06-01T00:00:00",
                "predicted_value": 150,
                "actual_value": 145,
                "probability": 0.87,
                "confidence_interval_lower": 120,
                "confidence_interval_upper": 180,
                "alert_level": "medium",
                "trend": "up",
                "seasonality_coefficient": 1.2,
                "created_at": "2025-06-01T10:30:00.000000",
                "updated_at": "2025-06-01T10:30:00.000000"
            }
        }

class PredictionMetricsBase(SQLModel):
    """
    Modelo base para métricas de rendimiento de los modelos de predicción.
    
    Este modelo registra el rendimiento de los modelos de predicción, permitiendo
    realizar un seguimiento de su precisión y eficacia a lo largo del tiempo.
    """
    model_version: str = Field(
        ..., 
        max_length=50, 
        description="Versión o identificador del modelo evaluado"
    )
    accuracy: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Precisión del modelo (0-1), donde 1 es el mejor valor posible"
    )
    mae: float = Field(
        ..., 
        ge=0, 
        description="Error Absoluto Medio (MAE) - Error promedio de las predicciones"
    )
    mse: float = Field(
        ..., 
        ge=0, 
        description="Error Cuadrático Medio (MSE) - Penaliza más los errores grandes"
    )
    r2_score: float = Field(
        ..., 
        description="""
        Coeficiente de determinación (R²) - Proporción de la varianza explicada por el modelo.
        Valores más cercanos a 1 indican mejor ajuste.
        """
    )
    trained_at: datetime = Field(
        default_factory=datetime.utcnow, 
        nullable=False,
        description="Fecha y hora en que se entrenó el modelo"
    )
    training_duration: Optional[float] = Field(
        None, 
        ge=0, 
        description="Duración del entrenamiento en segundos"
    )
    features_used: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Lista de características utilizadas por el modelo"
    )
    parameters: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Hiperparámetros y configuración del modelo"
    )
    medication_id: Optional[int] = Field(
        None, 
        foreign_key="medications.id",
        description="""
        ID del medicamento específico para estas métricas.
        Si es None, las métricas son globales para todos los medicamentos.
        """
    )

class PredictionMetrics(PredictionMetricsBase, table=True):
    """
    Modelo para almacenar métricas de rendimiento de los modelos de predicción.
    
    Este modelo registra el rendimiento de los modelos de predicción, permitiendo
    realizar un seguimiento de su precisión y eficacia a lo largo del tiempo.
    """
    __tablename__ = "prediction_metrics"
    
    id: Optional[int] = Field(
        default=None, 
        primary_key=True,
        description="Identificador único de las métricas"
    )
    
    # Relación con Prediction
    predictions: List["Prediction"] = Relationship(back_populates="metrics", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    created_at: datetime = Field(
        default_factory=datetime.utcnow, 
        nullable=False,
        description="Fecha y hora de creación del registro"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, 
        nullable=False,
        description="Fecha y hora de la última actualización"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, 
        nullable=False,
        description="Fecha y hora de creación del registro"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, 
        nullable=False,
        description="Fecha y hora de la última actualización"
    )
    
    model_version: str = Field(
        ..., 
        max_length=50, 
        description="Versión o identificador del modelo evaluado"
    )
    accuracy: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Precisión del modelo (0-1), donde 1 es el mejor valor posible"
    )
    mae: float = Field(
        ..., 
        ge=0, 
        description="Error Absoluto Medio (MAE) - Error promedio de las predicciones"
    )
    mse: float = Field(
        ..., 
        ge=0, 
        description="Error Cuadrático Medio (MSE) - Penaliza más los errores grandes"
    )
    r2_score: float = Field(
        ..., 
        description="""
        Coeficiente de determinación (R²) - Proporción de la varianza explicada por el modelo.
        Valores más cercanos a 1 indican mejor ajuste.
        """
    )
    trained_at: datetime = Field(
        default_factory=datetime.utcnow, 
        nullable=False,
        description="Fecha y hora en que se entrenó el modelo"
    )
    training_duration: Optional[float] = Field(
        None, 
        ge=0, 
        description="Duración del entrenamiento en segundos"
    )
    features_used: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Lista de características utilizadas por el modelo"
    )
    parameters: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Hiperparámetros y configuración del modelo"
    )
    medication_id: Optional[int] = Field(
        None, 
        foreign_key="medications.id",
        description="""
        ID del medicamento específico para estas métricas.
        Si es None, las métricas son globales para todos los medicamentos.
        """
    )
    
    # Relación inversa con las predicciones generadas por este modelo
    predictions: List["Prediction"] = Relationship(back_populates="metrics")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        
        schema_extra = {
            "example": {
                "model_version": "v1.2.3",
                "accuracy": 0.95,
                "mae": 12.5,
                "mse": 250.75,
                "r2_score": 0.92,
                "training_duration": 3600.5,
                "features_used": ["sales_history", "seasonality", "price"],
                "parameters": {"n_estimators": 100, "max_depth": 10},
                "medication_id": 1
            }
        }

class PredictionMetricsCreate(SQLModel):
    """
    Modelo para crear nuevas métricas de predicción.
    
    Se utiliza para validar los datos de entrada al registrar métricas
    de un modelo de predicción.
    """
    model_version: str = Field(
        ...,
        description="Versión o identificador del modelo evaluado"
    )
    accuracy: float = Field(
        ...,
        ge=0,
        le=1,
        description="Precisión del modelo (0-1)"
    )
    mae: float = Field(
        ...,
        ge=0,
        description="Error Absoluto Medio (MAE)"
    )
    mse: float = Field(
        ...,
        ge=0,
        description="Error Cuadrático Medio (MSE)"
    )
    r2_score: float = Field(
        ...,
        description="Coeficiente de determinación (R²)"
    )
    training_duration: Optional[float] = Field(
        None,
        ge=0,
        description="Duración del entrenamiento en segundos"
    )
    features_used: List[str] = Field(
        default_factory=list,
        description="Lista de características utilizadas por el modelo"
    )
    parameters: dict = Field(
        default_factory=dict,
        description="Hiperparámetros y configuración del modelo"
    )
    medication_id: Optional[int] = Field(
        None,
        description="ID del medicamento específico (opcional, para modelos específicos)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "model_version": "v1.2.3",
                "accuracy": 0.95,
                "mae": 12.5,
                "mse": 250.75,
                "r2_score": 0.92,
                "training_duration": 3600.5,
                "features_used": ["sales_history", "seasonality", "price"],
                "parameters": {"n_estimators": 100, "max_depth": 10},
                "medication_id": 1
            }
        }

class PredictionMetricsResponse(PredictionMetricsBase):
    """
    Modelo de respuesta para las métricas de predicción.
    
    Hereda de PredictionMetricsBase pero con configuraciones específicas para respuestas API.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        
        schema_extra = {
            "example": {
                "id": 1,
                "created_at": "2025-06-05T15:30:00.000000",
                "updated_at": "2025-06-05T15:30:00.000000",
                "model_version": "v1.2.3",
                "accuracy": 0.95,
                "mae": 12.5,
                "mse": 250.75,
                "r2_score": 0.92,
                "trained_at": "2025-06-05T15:30:00.000000",
                "training_duration": 3600.5,
                "features_used": ["sales_history", "seasonality", "price"],
                "parameters": {"n_estimators": 100, "max_depth": 10},
                "medication_id": 1
            }
        }

class PredictionMetricsUpdate(SQLModel):
    """
    Modelo para actualizar métricas de predicción existentes.
    
    Todos los campos son opcionales. Solo se actualizarán los campos proporcionados.
    """
    accuracy: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Nueva precisión del modelo (0-1)"
    )
    mae: Optional[float] = Field(
        None,
        ge=0,
        description="Nuevo Error Absoluto Medio (MAE)"
    )
    mse: Optional[float] = Field(
        None,
        ge=0,
        description="Nuevo Error Cuadrático Medio (MSE)"
    )
    r2_score: Optional[float] = Field(
        None,
        description="Nuevo Coeficiente de determinación (R²)"
    )
    training_duration: Optional[float] = Field(
        None,
        ge=0,
        description="Nueva duración del entrenamiento en segundos"
    )
    parameters: Optional[dict] = Field(
        None,
        description="Nuevos hiperparámetros y configuración del modelo"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        
        schema_extra = {
            "example": {
                "accuracy": 0.96,
                "mae": 12.0,
                "training_duration": 3800.25
            }
        }