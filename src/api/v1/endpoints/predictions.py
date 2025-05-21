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

# Simple database session dependency
def get_db_session():
    db = get_db()
    try:
        yield db
    finally:
        db.close()

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
    "/predict/{medication_id}",
    response_model=PredictionResponse,
    tags=["predictions"]
)
async def predict_shortage(
    medication_id: int = Path(..., description="ID del medicamento"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> PredictionResponse:
    try:
        # Mock response for testing
        return PredictionResponse(
            medication_id=medication_id,
            prediction="Sí",
            probability=0.85
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Evaluate endpoint
@router.get(
    "/evaluate/{medication_id}",
    response_model=EvaluationResponse,
    tags=["predictions"]
)
async def evaluate_model(
    medication_id: int = Path(..., description="ID del medicamento"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> EvaluationResponse:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos suficientes"
        )
    
    try:
        # Mock response for testing
        return EvaluationResponse(
            model_type="RandomForest",
            metrics={"accuracy": 0.95}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )