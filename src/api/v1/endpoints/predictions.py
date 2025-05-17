from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.services.prediction_service import PredictionService

router = APIRouter()

@router.get("/predict/{medicamento_id}")
def predict_shortage(medicamento_id: int, db: Session = Depends(get_db)):
    try:
        result = PredictionService.predict_shortages(db, medicamento_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/evaluate/{medicamento_id}")
def evaluate_model(medicamento_id: int, db: Session = Depends(get_db)):
    try:
        result = PredictionService.evaluate_model(db, medicamento_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))