
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from src.dependencies import get_db
from src.services.prediction_service import get_predictions, run_prediction_model
from src.models.prediction import PredictionResponse
from typing import List

router = APIRouter()

@router.get("/", response_model=List[PredictionResponse])
def read_predictions(db: Session = Depends(get_db)):
    predictions = get_predictions(db)
    return predictions

@router.post("/run", status_code=201)
async def run_predictions(db: Session = Depends(get_db)):
    result = run_prediction_model(db)
    return result
