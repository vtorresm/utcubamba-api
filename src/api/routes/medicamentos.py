from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from src.db.database import get_db
from src.models.schemas import Medicamento, MedicamentoCreate
from src.models.database_models import Medicamento as MedicamentoModel
from src.api.dependencies import get_current_user, require_role
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Medicamento)
def create_medicamento(medicamento: MedicamentoCreate, current_user: MedicamentoModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to create medicamento: {medicamento.nombre_comercial}")
    db_medicamento = MedicamentoModel(**medicamento.dict())
    db.add(db_medicamento)
    try:
        db.commit()
        db.refresh(db_medicamento)
        logger.info(f"Medicamento created successfully: {medicamento.nombre_comercial}")
        return db_medicamento
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to create medicamento: Barcode {medicamento.codigo_barras} already exists")
        raise HTTPException(status_code=400, detail="Barcode already exists")

@router.get("/", response_model=List[Medicamento])
def read_medicamentos(skip: int = 0, limit: int = 100, current_user: MedicamentoModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Listing medicamentos (skip={skip}, limit={limit}) by admin: {current_user.email}")
    medicamentos = db.query(MedicamentoModel).offset(skip).limit(limit).all()
    logger.debug(f"Retrieved {len(medicamentos)} medicamentos")
    return medicamentos

@router.get("/{medicamento_id}", response_model=Medicamento)
def read_medicamento(medicamento_id: int, current_user: MedicamentoModel = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Fetching medicamento ID: {medicamento_id} by user: {current_user.email}")
    medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == medicamento_id).first()
    if not medicamento:
        logger.error(f"Medicamento ID: {medicamento_id} not found")
        raise HTTPException(status_code=404, detail="Medicamento not found")
    logger.debug(f"Medicamento retrieved: {medicamento.nombre_comercial}")
    return medicamento

@router.put("/{medicamento_id}", response_model=Medicamento)
def update_medicamento(medicamento_id: int, medicamento: MedicamentoCreate, current_user: MedicamentoModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to update medicamento ID: {medicamento_id} by admin: {current_user.email}")
    db_medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == medicamento_id).first()
    if not db_medicamento:
        logger.error(f"Medicamento ID: {medicamento_id} not found for update")
        raise HTTPException(status_code=404, detail="Medicamento not found")
    
    for key, value in medicamento.dict().items():
        setattr(db_medicamento, key, value)
    
    try:
        db.commit()
        db.refresh(db_medicamento)
        logger.info(f"Medicamento updated successfully: {db_medicamento.nombre_comercial}")
        return db_medicamento
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to update medicamento: Barcode {medicamento.codigo_barras} already exists")
        raise HTTPException(status_code=400, detail="Barcode already exists")

@router.delete("/{medicamento_id}")
def delete_medicamento(medicamento_id: int, current_user: MedicamentoModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to delete medicamento ID: {medicamento_id} by admin: {current_user.email}")
    medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == medicamento_id).first()
    if not medicamento:
        logger.error(f"Medicamento ID: {medicamento_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Medicamento not found")
    db.delete(medicamento)
    db.commit()
    logger.info(f"Medicamento deleted successfully: {medicamento.nombre_comercial}")
    return {"message": "Medicamento deleted successfully"}