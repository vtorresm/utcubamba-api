from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.models.database_models import UsoHistorico as UsoHistoricoModel, Prediccion as PrediccionModel, Medicamento as MedicamentoModel, Alerta as AlertaModel, HistorialAlerta as HistorialAlertaModel
from src.models.schemas import UsoHistorico, UsoHistoricoCreate, Prediccion, PrediccionCreate
from src.api.dependencies import get_current_user, require_role
from src.utils.prediction_utils import predict_usage  # Nueva importación
import logging
from datetime import datetime, timedelta
from src.utils.email_utils import send_email

router = APIRouter()
logger = logging.getLogger(__name__)

def update_stock_and_check_alerts_pred(medicamento: MedicamentoModel, stock_simulado: float, db: Session):
    """Verifica y genera alertas basadas en el stock simulado después de la predicción."""
    # Verificar alerta de "Stock bajo"
    if stock_simulado <= 15:
        existing_alerta = db.query(AlertaModel).filter(
            AlertaModel.medicamento_id == medicamento.medicamento_id,
            AlertaModel.tipo_alerta == "Stock bajo",
            AlertaModel.estado == "Pendiente"
        ).first()
        if not existing_alerta:
            alerta = AlertaModel(
                medicamento_id=medicamento.medicamento_id,
                tipo_alerta="Stock bajo",
                estado="Pendiente",
                fecha_creacion=datetime.utcnow()
            )
            db.add(alerta)
            db.commit()
            db.refresh(alerta)
            historial = HistorialAlertaModel(
                alerta_id=alerta.alerta_id,
                accion="Creada",
                fecha=datetime.utcnow(),
                observaciones=f"Alerta creada: Stock bajo ({stock_simulado} unidades)"
            )
            db.add(historial)
            db.commit()
            send_email(
                subject=f"Nueva Alerta: Stock bajo para {medicamento.nombre_comercial}",
                body=f"Se ha generado una alerta de stock bajo para el medicamento {medicamento.nombre_comercial}. Stock actual: {stock_simulado} unidades."
            )
            logger.info(f"Alerta creada para medicamento {medicamento.medicamento_id}: Stock bajo ({stock_simulado} unidades)")

    # Verificar alerta de "Stock muy bajo"
    if 6 < stock_simulado <= 15:
        existing_alerta = db.query(AlertaModel).filter(
            AlertaModel.medicamento_id == medicamento.medicamento_id,
            AlertaModel.tipo_alerta == "Stock muy bajo",
            AlertaModel.estado == "Pendiente"
        ).first()
        if not existing_alerta:
            alerta = AlertaModel(
                medicamento_id=medicamento.medicamento_id,
                tipo_alerta="Stock muy bajo",
                estado="Pendiente",
                fecha_creacion=datetime.utcnow()
            )
            db.add(alerta)
            db.commit()
            db.refresh(alerta)
            historial = HistorialAlertaModel(
                alerta_id=alerta.alerta_id,
                accion="Creada",
                fecha=datetime.utcnow(),
                observaciones=f"Alerta creada: Stock muy bajo ({stock_simulado} unidades)"
            )
            db.add(historial)
            db.commit()
            send_email(
                subject=f"Nueva Alerta: Stock muy bajo para {medicamento.nombre_comercial}",
                body=f"Se ha generado una alerta de stock muy bajo para el medicamento {medicamento.nombre_comercial}. Stock actual: {stock_simulado} unidades."
            )
            logger.info(f"Alerta creada para medicamento {medicamento.medicamento_id}: Stock muy bajo ({stock_simulado} unidades)")

    # Verificar alerta de "Próximo a vencer"
    if medicamento.fecha_vencimiento:
        days_to_expiry = (medicamento.fecha_vencimiento - datetime.utcnow()).days
        if days_to_expiry <= 30:
            existing_alerta = db.query(AlertaModel).filter(
                AlertaModel.medicamento_id == medicamento.medicamento_id,
                AlertaModel.tipo_alerta == "Próximo a vencer",
                AlertaModel.estado == "Pendiente"
            ).first()
            if not existing_alerta:
                alerta = AlertaModel(
                    medicamento_id=medicamento.medicamento_id,
                    tipo_alerta="Próximo a vencer",
                    estado="Pendiente",
                    fecha_creacion=datetime.utcnow()
                )
                db.add(alerta)
                db.commit()
                db.refresh(alerta)
                historial = HistorialAlertaModel(
                    alerta_id=alerta.alerta_id,
                    accion="Creada",
                    fecha=datetime.utcnow(),
                    observaciones=f"Alerta creada: Próximo a vencer (vence en {days_to_expiry} días)"
                )
                db.add(historial)
                db.commit()
                send_email(
                    subject=f"Nueva Alerta: Próximo a vencer para {medicamento.nombre_comercial}",
                    body=f"Se ha generado una alerta de vencimiento para el medicamento {medicamento.nombre_comercial}. Vence en {days_to_expiry} días."
                )
                logger.info(f"Alerta creada para medicamento {medicamento.medicamento_id}: Próximo a vencer (vence en {days_to_expiry} días)")

    # Verificar alerta de "Stock crítico"
    if stock_simulado <= 5:
        existing_alerta = db.query(AlertaModel).filter(
            AlertaModel.medicamento_id == medicamento.medicamento_id,
            AlertaModel.tipo_alerta == "Stock crítico",
            AlertaModel.estado == "Pendiente"
        ).first()
        if not existing_alerta:
            alerta = AlertaModel(
                medicamento_id=medicamento.medicamento_id,
                tipo_alerta="Stock crítico",
                estado="Pendiente",
                fecha_creacion=datetime.utcnow()
            )
            db.add(alerta)
            db.commit()
            db.refresh(alerta)
            historial = HistorialAlertaModel(
                alerta_id=alerta.alerta_id,
                accion="Creada",
                fecha=datetime.utcnow(),
                observaciones=f"Alerta creada: Stock crítico ({stock_simulado} unidades)"
            )
            db.add(historial)
            db.commit()
            send_email(
                subject=f"Nueva Alerta: Stock crítico para {medicamento.nombre_comercial}",
                body=f"Se ha generado una alerta de stock crítico para el medicamento {medicamento.nombre_comercial}. Stock actual: {stock_simulado} unidades."
            )
            logger.info(f"Alerta creada para medicamento {medicamento.medicamento_id}: Stock crítico ({stock_simulado} unidades)")

    # Verificar alerta de "Stock negativo"
    if stock_simulado < 0:
        existing_alerta = db.query(AlertaModel).filter(
            AlertaModel.medicamento_id == medicamento.medicamento_id,
            AlertaModel.tipo_alerta == "Stock negativo",
            AlertaModel.estado == "Pendiente"
        ).first()
        if not existing_alerta:
            alerta = AlertaModel(
                medicamento_id=medicamento.medicamento_id,
                tipo_alerta="Stock negativo",
                estado="Pendiente",
                fecha_creacion=datetime.utcnow()
            )
            db.add(alerta)
            db.commit()
            db.refresh(alerta)
            historial = HistorialAlertaModel(
                alerta_id=alerta.alerta_id,
                accion="Creada",
                fecha=datetime.utcnow(),
                observaciones=f"Alerta creada: Stock negativo ({stock_simulado} unidades)"
            )
            db.add(historial)
            db.commit()
            send_email(
                subject=f"Nueva Alerta: Stock negativo para {medicamento.nombre_comercial}",
                body=f"Se ha generado una alerta de stock negativo para el medicamento {medicamento.nombre_comercial}. Stock actual: {stock_simulado} unidades."
            )
            logger.info(f"Alerta creada para medicamento {medicamento.medicamento_id}: Stock negativo ({stock_simulado} unidades)")

    # Verificar alerta de "Sobreinventario"
    if medicamento.stock_maximo and stock_simulado > medicamento.stock_maximo:
        existing_alerta = db.query(AlertaModel).filter(
            AlertaModel.medicamento_id == medicamento.medicamento_id,
            AlertaModel.tipo_alerta == "Sobreinventario",
            AlertaModel.estado == "Pendiente"
        ).first()
        if not existing_alerta:
            alerta = AlertaModel(
                medicamento_id=medicamento.medicamento_id,
                tipo_alerta="Sobreinventario",
                estado="Pendiente",
                fecha_creacion=datetime.utcnow()
            )
            db.add(alerta)
            db.commit()
            db.refresh(alerta)
            historial = HistorialAlertaModel(
                alerta_id=alerta.alerta_id,
                accion="Creada",
                fecha=datetime.utcnow(),
                observaciones=f"Alerta creada: Sobreinventario ({stock_simulado} unidades, máximo: {medicamento.stock_maximo})"
            )
            db.add(historial)
            db.commit()
            send_email(
                subject=f"Nueva Alerta: Sobreinventario para {medicamento.nombre_comercial}",
                body=f"Se ha generado una alerta de sobreinventario para el medicamento {medicamento.nombre_comercial}. Stock actual: {stock_simulado} unidades, máximo permitido: {medicamento.stock_maximo}."
            )
            logger.info(f"Alerta creada para medicamento {medicamento.medicamento_id}: Sobreinventario ({stock_simulado} unidades)")

@router.post("/uso-historico/", response_model=UsoHistorico)
def create_uso_historico(
    uso_historico: UsoHistoricoCreate,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Creating uso historico by admin: {current_user.email}")
    db_uso = UsoHistoricoModel(**uso_historico.dict())
    db.add(db_uso)
    db.commit()
    db.refresh(db_uso)
    logger.info(f"Uso historico created: {db_uso.historico_id}")
    return db_uso

@router.get("/uso-historico/", response_model=list[UsoHistorico])
def get_uso_historico(
    medicamento_id: int = None,
    mes: int = None,
    anio: int = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Fetching uso historico by admin: {current_user.email}")
    query = db.query(UsoHistoricoModel)
    if medicamento_id:
        query = query.filter(UsoHistoricoModel.medicamento_id == medicamento_id)
    if mes:
        query = query.filter(UsoHistoricoModel.mes == mes)
    if anio:
        query = query.filter(UsoHistoricoModel.anio == anio)
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=Prediccion)
def create_prediccion(
    prediccion: PrediccionCreate,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Creating prediccion by admin: {current_user.email}")

    # Verificar que el medicamento existe
    medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == prediccion.medicamento_id).first()
    if not medicamento:
        logger.error(f"Medicamento {prediccion.medicamento_id} not found")
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")

    # Preparar datos para predicción
    prediction_data = {
        "medicamento_id": str(prediccion.medicamento_id),
        "mes": prediccion.mes,
        "anio": prediccion.anio,
        "region": prediccion.region,
        "temporada": prediccion.temporada,
        "uso_previsto": prediccion.uso_previsto,
        "uso_prev_dif": 0  # Asumimos 0 si no se proporciona
    }

    # Realizar la predicción usando prediction_utils
    try:
        uso_predicho = predict_usage(prediction_data)
    except Exception as e:
        logger.error(f"Error al realizar la predicción: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al realizar la predicción: {str(e)}")

    # Actualizar stock_actual restando uso_predicho
    medicamento.stock_actual -= int(uso_predicho)  # Convertir a entero para evitar decimales en stock
    stock_simulado = medicamento.stock_actual

    # Actualizar estado del medicamento
    if stock_simulado < 0:
        medicamento.disponibilidad = "Stock Negativo"
    elif stock_simulado == 0:
        medicamento.disponibilidad = "Agotado"
    elif stock_simulado <= 15:
        medicamento.disponibilidad = "Stock Bajo"
    else:
        medicamento.disponibilidad = "En Stock"

    db.commit()
    db.refresh(medicamento)

    # Guardar predicción
    db_prediccion = PrediccionModel(
        medicamento_id=prediccion.medicamento_id,
        mes=prediccion.mes,
        anio=prediccion.anio,
        region=prediccion.region,
        temporada=prediccion.temporada,
        uso_previsto=prediccion.uso_previsto,
        uso_predicho=uso_predicho
    )
    db.add(db_prediccion)
    db.commit()
    db.refresh(db_prediccion)

    # Verificar y generar alertas basadas en el stock actualizado
    update_stock_and_check_alerts_pred(medicamento, stock_simulado, db)

    logger.info(f"Prediccion created: {db_prediccion.prediccion_id}")
    return db_prediccion

@router.get("/", response_model=list[Prediccion])
def get_predicciones(
    medicamento_id: int = None,
    mes: int = None,
    anio: int = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: MedicamentoModel = Depends(require_role("admin"))
):
    logger.info(f"Fetching predicciones by admin: {current_user.email}")
    query = db.query(PrediccionModel)
    if medicamento_id:
        query = query.filter(PrediccionModel.medicamento_id == medicamento_id)
    if mes:
        query = query.filter(PrediccionModel.mes == mes)
    if anio:
        query = query.filter(PrediccionModel.anio == anio)
    return query.offset(skip).limit(limit).all()