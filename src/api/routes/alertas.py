from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from src.db.database import get_db
from src.models.database_models import Alerta as AlertaModel, HistorialAlerta as HistorialAlertaModel, Medicamento as MedicamentoModel
from src.models.schemas import Alerta, AlertaCreate, AlertaUpdate, HistorialAlerta, HistorialAlertaCreate
from src.api.dependencies import get_current_user, require_role
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Alerta])
def get_alertas(
    medicamento: Optional[str] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Fetching alertas by admin: {current_user.email}")

    query = db.query(AlertaModel).join(MedicamentoModel)

    if medicamento:
        query = query.filter(MedicamentoModel.nombre_comercial.ilike(f"%{medicamento}%"))
    if estado:
        query = query.filter(AlertaModel.estado == estado)

    alertas = query.offset(skip).limit(limit).all()
    return alertas

@router.post("/", response_model=Alerta)
def create_alerta(
    alerta: AlertaCreate,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Creating alerta by admin: {current_user.email}")

    medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == alerta.medicamento_id).first()
    if not medicamento:
        logger.error(f"Medicamento {alerta.medicamento_id} not found")
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")

    # Verificar si ya existe una alerta pendiente para este medicamento
    existing_alerta = db.query(AlertaModel).filter(
        AlertaModel.medicamento_id == alerta.medicamento_id,
        AlertaModel.estado == "Pendiente"
    ).first()
    if existing_alerta:
        logger.warning(f"Alerta pendiente ya existe para medicamento {alerta.medicamento_id}")
        raise HTTPException(status_code=400, detail="Ya existe una alerta pendiente para este medicamento")

    db_alerta = AlertaModel(
        medicamento_id=alerta.medicamento_id,
        tipo_alerta=alerta.tipo_alerta,
        estado=alerta.estado,
        fecha_creacion=datetime.utcnow()
    )
    db.add(db_alerta)
    db.commit()
    db.refresh(db_alerta)

    # Registrar en el historial
    historial = HistorialAlertaModel(
        alerta_id=db_alerta.alerta_id,
        accion="Creada",
        fecha=datetime.utcnow(),
        observaciones=f"Alerta creada manualmente: {alerta.tipo_alerta}"
    )
    db.add(historial)
    db.commit()

    logger.info(f"Alerta created: {db_alerta.alerta_id}")
    return db_alerta

@router.put("/{alerta_id}", response_model=Alerta)
def update_alerta(
    alerta_id: int,
    alerta_update: AlertaUpdate,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Updating alerta {alerta_id} by admin: {current_user.email}")

    db_alerta = db.query(AlertaModel).filter(AlertaModel.alerta_id == alerta_id).first()
    if not db_alerta:
        logger.error(f"Alerta {alerta_id} not found")
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    db_alerta.estado = alerta_update.estado
    db_alerta.fecha_actualizacion = datetime.utcnow()
    db.commit()
    db.refresh(db_alerta)

    # Registrar en el historial
    accion = "Resuelta" if alerta_update.estado == "Resuelta" else "Actualizada"
    historial = HistorialAlertaModel(
        alerta_id=db_alerta.alerta_id,
        accion=accion,
        fecha=datetime.utcnow(),
        observaciones=alerta_update.observaciones or f"Alerta actualizada a estado: {alerta_update.estado}"
    )
    db.add(historial)
    db.commit()

    logger.info(f"Alerta updated: {db_alerta.alerta_id}")
    return db_alerta

@router.delete("/{alerta_id}")
def delete_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Deleting alerta {alerta_id} by admin: {current_user.email}")

    db_alerta = db.query(AlertaModel).filter(AlertaModel.alerta_id == alerta_id).first()
    if not db_alerta:
        logger.error(f"Alerta {alerta_id} not found")
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    # Registrar en el historial antes de eliminar
    historial = HistorialAlertaModel(
        alerta_id=db_alerta.alerta_id,
        accion="Eliminada",
        fecha=datetime.utcnow(),
        observaciones="Alerta eliminada manualmente"
    )
    db.add(historial)
    db.commit()

    db.delete(db_alerta)
    db.commit()

    logger.info(f"Alerta deleted: {alerta_id}")
    return {"detail": "Alerta eliminada"}

@router.get("/historial", response_model=List[HistorialAlerta])
def get_historial_alertas(
    alerta_id: Optional[int] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Fetching historial de alertas by admin: {current_user.email}")

    query = db.query(HistorialAlertaModel)

    if alerta_id:
        query = query.filter(HistorialAlertaModel.alerta_id == alerta_id)
    if fecha_desde:
        query = query.filter(HistorialAlertaModel.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(HistorialAlertaModel.fecha <= fecha_hasta)

    historial = query.offset(skip).limit(limit).all()
    return historial