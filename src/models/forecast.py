"""
Modelos para predicciones de series de tiempo con ARIMA y Prophet.

ForecastRun   — representa una ejecución de forecasting para un medicamento
               con un modelo específico (arima / prophet / random_forest / ensemble).
ForecastPoint — cada punto futuro de la serie: fecha, valor predicho e intervalo
               de confianza al 95%.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .medication import Medication


# ─── ForecastRun ────────────────────────────────────────────────────────────

class ForecastRunBase(SQLModel):
    medication_id: int = Field(foreign_key="medications.id", index=True)
    model_type: str = Field(
        ..., max_length=30,
        description="Tipo de modelo: 'arima', 'prophet', 'random_forest', 'ensemble'"
    )
    horizon_days: int = Field(
        default=30, ge=1, le=365,
        description="Horizonte de predicción en días"
    )
    # Métricas de evaluación (calculadas sobre el set de validación)
    mae: Optional[float] = Field(default=None, ge=0, description="Mean Absolute Error")
    mape: Optional[float] = Field(default=None, ge=0, description="Mean Absolute Percentage Error")
    rmse: Optional[float] = Field(default=None, ge=0, description="Root Mean Squared Error")
    r2: Optional[float] = Field(default=None, description="R² score")
    # Parámetros del modelo (e.g. ARIMA order, Prophet seasonality config)
    parameters: Optional[dict] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    # Contexto al momento del forecast
    stock_at_forecast: Optional[float] = Field(
        default=None, description="Stock del medicamento cuando se ejecutó el forecast"
    )
    days_until_shortage: Optional[int] = Field(
        default=None, description="Días estimados hasta desabastecimiento"
    )
    shortage_probability: Optional[float] = Field(
        default=None, ge=0, le=1,
        description="Probabilidad de desabastecimiento en el horizonte"
    )
    alert_level: Optional[str] = Field(
        default=None, max_length=20,
        description="Nivel de alerta: 'low', 'medium', 'high'"
    )


class ForecastRun(ForecastRunBase, table=True):
    __tablename__ = "forecast_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    medication: Optional["Medication"] = Relationship()
    points: List["ForecastPoint"] = Relationship(
        back_populates="run",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ForecastRunCreate(ForecastRunBase):
    pass


class ForecastRunResponse(ForecastRunBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── ForecastPoint ──────────────────────────────────────────────────────────

class ForecastPointBase(SQLModel):
    forecast_run_id: int = Field(foreign_key="forecast_runs.id", index=True)
    date: datetime = Field(..., description="Fecha del punto de predicción")
    predicted_value: float = Field(..., ge=0, description="Consumo predicho (unidades/día)")
    lower_ci: Optional[float] = Field(default=None, ge=0, description="Límite inferior IC 95%")
    upper_ci: Optional[float] = Field(default=None, ge=0, description="Límite superior IC 95%")


class ForecastPoint(ForecastPointBase, table=True):
    __tablename__ = "forecast_points"

    id: Optional[int] = Field(default=None, primary_key=True)
    run: Optional["ForecastRun"] = Relationship(back_populates="points")


class ForecastPointResponse(ForecastPointBase):
    id: int

    class Config:
        from_attributes = True


# ─── Respuesta completa ──────────────────────────────────────────────────────

class ForecastFullResponse(ForecastRunResponse):
    """ForecastRun + sus puntos de serie temporal."""
    points: List[ForecastPointResponse] = []
    medication_name: Optional[str] = None

    class Config:
        from_attributes = True
