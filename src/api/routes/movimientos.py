from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.db.database import get_db
from src.models.database_models import Movimiento as MovimientoModel, Medicamento as MedicamentoModel, Alerta as AlertaModel, HistorialAlerta as HistorialAlertaModel
from src.models.schemas import Movimiento, MovimientoCreate
from src.api.dependencies import get_current_user, require_role
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

def update_stock_and_check_alerts(medicamento: MedicamentoModel, movimiento: MovimientoModel, db: Session):
    """Actualiza el stock del medicamento y genera alertas si es necesario."""
    if movimiento.tipo_movimiento.value == "Entrada":
        medicamento.stock_actual += movimiento.cantidad
    elif movimiento.tipo_movimiento.value == "Salida":
        if medicamento.stock_actual < movimiento.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente para realizar la salida")
        medicamento.stock_actual -= movimiento.cantidad

    # Actualizar estado del medicamento
    if medicamento.stock_actual == 0:
        medicamento.disponibilidad = "Agotado"
    elif medicamento.stock_actual <= 10:
        medicamento.disponibilidad = "Stock Bajo"
    else:
        medicamento.disponibilidad = "En Stock"

    db.commit()
    db.refresh(medicamento)

    # Verificar si se debe generar una alerta
    if medicamento.stock_actual <= 10:
        # Verificar si ya existe una alerta pendiente para este medicamento
        existing_alerta = db.query(AlertaModel).filter(
            AlertaModel.medicamento_id == medicamento.medicamento_id,
            AlertaModel.estado == "Pendiente"
        ).first()

        if not existing_alerta:
            # Crear nueva alerta
            alerta = AlertaModel(
                medicamento_id=medicamento.medicamento_id,
                tipo_alerta="Stock bajo",
                estado="Pendiente",
                fecha_creacion=datetime.utcnow()
            )
            db.add(alerta)
            db.commit()
            db.refresh(alerta)

            # Registrar en el historial
            historial = HistorialAlertaModel(
                alerta_id=alerta.alerta_id,
                accion="Creada",
                fecha=datetime.utcnow(),
                observaciones=f"Alerta creada: Stock bajo ({medicamento.stock_actual} unidades)"
            )
            db.add(historial)
            db.commit()
            logger.info(f"Alerta creada para medicamento {medicamento.medicamento_id}: Stock bajo ({medicamento.stock_actual} unidades)")

@router.get("/", response_model=List[Movimiento])
def get_movimientos(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(get_current_user)
):
    movimientos = db.query(MovimientoModel).offset(skip).limit(limit).all()
    return movimientos

@router.post("/", response_model=Movimiento)
def create_movimiento(
    movimiento: MovimientoCreate,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Creating movimiento by admin: {current_user.email}")

    medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == movimiento.medicamento_id).first()
    if not medicamento:
        logger.error(f"Medicamento {movimiento.medicamento_id} not found")
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")

    db_movimiento = MovimientoModel(
        fecha=datetime.utcnow(),
        tipo_movimiento=movimiento.tipo_movimiento,
        medicamento_id=movimiento.medicamento_id,
        cantidad=movimiento.cantidad,
        observaciones=movimiento.observaciones
    )
    db.add(db_movimiento)
    db.commit()
    db.refresh(db_movimiento)

    # Actualizar stock y verificar alertas
    update_stock_and_check_alerts(medicamento, db_movimiento, db)

    logger.info(f"Movimiento created: {db_movimiento.movimiento_id}")
    return db_movimiento

@router.get("/{movimiento_id}", response_model=Movimiento)
def get_movimiento(
    movimiento_id: int,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(get_current_user)
):
    movimiento = db.query(MovimientoModel).filter(MovimientoModel.movimiento_id == movimiento_id).first()
    if not movimiento:
        logger.error(f"Movimiento {movimiento_id} not found")
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return movimiento

@router.delete("/{movimiento_id}")
def delete_movimiento(
    movimiento_id: int,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    movimiento = db.query(MovimientoModel).filter(MovimientoModel.movimiento_id == movimiento_id).first()
    if not movimiento:
        logger.error(f"Movimiento {movimiento_id} not found")
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")

    medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == movimiento.medicamento_id).first()

    # Revertir el stock
    if movimiento.tipo_movimiento.value == "Entrada":
        medicamento.stock_actual -= movimiento.cantidad
    elif movimiento.tipo_movimiento.value == "Salida":
        medicamento.stock_actual += movimiento.cantidad

    # Actualizar estado del medicamento
    if medicamento.stock_actual == 0:
        medicamento.disponibilidad = "Agotado"
    elif medicamento.stock_actual <= 10:
        medicamento.disponibilidad = "Stock Bajo"
    else:
        medicamento.disponibilidad = "En Stock"

    db.delete(movimiento)
    db.commit()

    # Verificar alertas después de revertir el stock
    update_stock_and_check_alerts(medicamento, movimiento, db)

    logger.info(f"Movimiento {movimiento_id} deleted by admin: {current_user.email}")
    return {"detail": "Movimiento eliminado"}