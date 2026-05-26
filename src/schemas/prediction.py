from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PredictionBase(BaseModel):
    medication_id: int
    date: datetime = Field(default_factory=datetime.utcnow)
    real_usage: float = 0.0
    predicted_usage: float = 0.0
    stock: float = 0.0
    month_of_year: int = Field(default=datetime.utcnow().month, ge=1, le=12)
    regional_demand: float = 0.0
    shortage: bool = False
    probability: Optional[float] = None
    alert_level: Optional[str] = None
    trend: Optional[str] = None

    class Config:
        from_attributes = True


class PredictionCreate(PredictionBase):
    pass


class PredictionResponse(PredictionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    seasonality_coefficient: Optional[float] = None

    class Config:
        from_attributes = True


class PredictionMetricsBase(BaseModel):
    model_version: str
    accuracy: float = Field(..., ge=0, le=1)
    mae: float = Field(..., ge=0)
    mse: float = Field(..., ge=0)
    r2_score: float = Field(...)
    medication_id: Optional[int] = None

    class Config:
        from_attributes = True


class PredictionMetricsCreate(PredictionMetricsBase):
    training_duration: Optional[float] = None
    features_used: List[str] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)


class PredictionMetricsResponse(PredictionMetricsBase):
    id: int
    trained_at: datetime
    training_duration: Optional[float] = None
    features_used: List[str] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
