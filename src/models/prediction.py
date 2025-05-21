from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .medication import Medication
    from .movement import Movement

class PredictionBase(SQLModel):
    """Base model for Prediction with common attributes."""
    date: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    real_usage: float = Field(..., gt=0, description="Actual usage (R_i)")
    predicted_usage: float = Field(..., gt=0, description="Predicted usage (P_i)")
    stock: float = Field(..., ge=0, description="Available stock")
    month_of_year: int = Field(..., ge=1, le=12, description="Month of year (1-12)")
    regional_demand: float = Field(..., ge=0, description="Regional demand")
    restock_time: Optional[float] = Field(None, ge=0, description="Restock time in days")
    shortage: bool = Field(False, description="True if shortage occurred, False otherwise")
    probability: Optional[float] = Field(None, ge=0, le=1, description="Shortage probability (0-1)")
    
    # Foreign keys
    medication_id: int = Field(foreign_key="medications.id")
    movement_id: Optional[int] = Field(default=None, foreign_key="movements.id")

class Prediction(PredictionBase, table=True):
    """Prediction model for database."""
    __tablename__ = "predictions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Relationships
    medication: "Medication" = Relationship(back_populates="predictions")
    movement: Optional["Movement"] = Relationship(back_populates="prediction")

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