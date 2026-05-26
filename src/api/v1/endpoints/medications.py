from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

from src.core.database import get_db
from src.schemas.medication import MedicationResponse, MedicationCreate, MedicationUpdate
from src.services import medication_service
from src.dependencies.auth import get_current_user
from src.models.user import User, Role

router = APIRouter()


@router.get(
    "/test",
    summary="Endpoint de prueba",
    description="Verifica que el módulo de medicamentos esté funcionando correctamente.",
)
def test_endpoint():
    return {"message": "El endpoint de medicamentos está funcionando correctamente"}


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Listar medicamentos",
)
def get_medications(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    intake_type_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medications = medication_service.get_medications(
        db=db, skip=skip, limit=limit,
        name=name, category_id=category_id,
        intake_type_id=intake_type_id
    )
    total = medication_service.get_medications_count(db=db)
    items = [MedicationResponse.model_validate(m) for m in medications]
    return {
        "status": "success",
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(items),
        "items": items,
    }


@router.get(
    "/{medication_id}",
    response_model=Dict[str, Any],
    summary="Obtener medicamento por ID",
)
def get_medication(
    medication_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medication = medication_service.get_medication_by_id(db=db, medication_id=medication_id)
    if medication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el medicamento con ID {medication_id}"
        )
    return {
        "status": "success",
        "data": MedicationResponse.model_validate(medication),
    }


@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
def create_medication(
    medication: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return medication_service.create_medication(db=db, medication_data=medication)


@router.put("/{medication_id}", response_model=MedicationResponse)
def update_medication(
    medication_id: int,
    medication: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return medication_service.update_medication(db=db, medication_id=medication_id, update_data=medication)


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    medication_service.delete_medication(db=db, medication_id=medication_id)
    return None
