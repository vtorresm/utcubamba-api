from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.models.database_models import Movimiento as MovimientoModel, Medicamento as MedicamentoModel
from src.models.schemas import Movimiento, MovimientoCreate
from src.api.dependencies import get_current_user, require_role
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Movimiento)
def create_movimiento(movimiento: MovimientoCreate, current_user: MedicamentoModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to create movimiento by admin: {current_user.email}")

    # Verificar que el medicamento exista
    db_medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == movimiento.medicamento_id).first()
    if not db_medicamento:
        logger.error(f"Medicamento ID {movimiento.medicamento_id} not found")
        raise HTTPException(status_code=404, detail="Medicamento not found")

    # Validar stock para salidas
    if movimiento.tipo_movimiento == "Salida":
        if db_medicamento.stock_actual < movimiento.cantidad:
            logger.error(f"Insufficient stock for medicamento ID {movimiento.medicamento_id}: {db_medicamento.stock_actual} available, {movimiento.cantidad} requested")
            raise HTTPException(status_code=400, detail="Insufficient stock for this operation")

    # Crear el movimiento
    db_movimiento = MovimientoModel(**movimiento.dict())
    db.add(db_movimiento)

    # Actualizar stock
    if movimiento.tipo_movimiento == "Entrada":
        db_medicamento.stock_actual += movimiento.cantidad
    else:  # Salida
        db_medicamento.stock_actual -= movimiento.cantidad

    # Actualizar disponibilidad dinámicamente
    if db_medicamento.stock_actual == 0:
        db_medicamento.disponibilidad = "Agotado"
    elif db_medicamento.stock_actual <= 10:
        db_medicamento.disponibilidad = "Stock Bajo"
    else:
        db_medicamento.disponibilidad = "En Stock"

    try:
        db.commit()
        db.refresh(db_movimiento)
        logger.info(f"Movimiento created successfully: {movimiento.tipo_movimiento} for medicamento ID {movimiento.medicamento_id}")
        return db_movimiento
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create movimiento: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create movimiento")