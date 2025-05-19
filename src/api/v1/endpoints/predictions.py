from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.services.prediction_service import PredictionService
from src.services.auth_service import AuthService, oauth2_scheme
from src.models.user import User, Role

router = APIRouter()

@router.get("/predict/{medicamento_id}", tags=["predictions"])
def predict_shortage(
    medicamento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Predice desabastecimiento para un medicamento.
    Requiere autenticación.
    """
    try:
        result = PredictionService.predict_shortages(db, medicamento_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/evaluate/{medicamento_id}", tags=["predictions"])
def evaluate_model(
    medicamento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Evalúa el modelo para un medicamento.
    Requiere autenticación y rol de administrador.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    try:
        result = PredictionService.evaluate_model(db, medicamento_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))