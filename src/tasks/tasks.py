from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from src.tasks.celery_config import celery_app
from src.models.prediction import Prediction, PredictionMetrics, PredictionMetricsCreate
from src.models.medication import Medication
from src.models.movement import Movement
from src.models.notification import Notification, NotificationLevel, NotificationType
from src.models.user import User, Role
from src.core.database import SessionLocal

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    try:
        db = SessionLocal()
        return db
    except Exception:
        raise


@celery_app.task(bind=True, max_retries=3)
def generate_predictions_for_all_medications(self):
    from src.services.prediction_service import predict_shortage_risk

    db = _get_db()
    try:
        medications = db.query(Medication).all()
        results = []
        for med in medications:
            try:
                result = predict_shortage_risk(db=db, medication_id=med.id, days_ahead=30)
                results.append({"medication_id": med.id, "status": "success", "risk_level": result.get("risk_level")})
            except Exception as e:
                logger.error("Error predicting for medication %s: %s", med.id, str(e))
                results.append({"medication_id": med.id, "status": "failed", "error": str(e)})

        _send_bulk_alert_notifications(db, results)
        return {"total": len(medications), "results": results}

    except Exception as e:
        logger.error("Error in generate_predictions_for_all_medications: %s", str(e))
        raise self.retry(exc=e, countdown=300)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def check_low_stock_medications(self):
    db = _get_db()
    try:
        low_stock = db.query(Medication).filter(
            Medication.stock <= Medication.min_stock
        ).all()

        admin_users = db.query(User).filter(
            User.role.in_([Role.ADMIN, Role.FARMACIA])
        ).all()

        notifications_created = 0
        for med in low_stock:
            for user in admin_users:
                notification = Notification(
                    user_id=user.id,
                    title=f"Stock bajo: {med.name}",
                    message=f"El medicamento '{med.name}' tiene {med.stock} unidades (mínimo: {med.min_stock}).",
                    type=NotificationType.STOCK_ALERT,
                    level=NotificationLevel.HIGH
                )
                db.add(notification)
                notifications_created += 1

        db.commit()
        return {
            "low_stock_count": len(low_stock),
            "notifications_created": notifications_created
        }

    except Exception as e:
        logger.error("Error in check_low_stock_medications: %s", str(e))
        raise self.retry(exc=e, countdown=300)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def cleanup_old_predictions(self, days_old: int = 365):
    db = _get_db()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        old_predictions = db.query(Prediction).filter(
            Prediction.created_at < cutoff
        ).all()

        count = len(old_predictions)
        for p in old_predictions:
            db.delete(p)
        db.commit()
        return {"deleted_predictions": count}

    except Exception as e:
        logger.error("Error in cleanup_old_predictions: %s", str(e))
        raise self.retry(exc=e, countdown=300)
    finally:
        db.close()


def _send_bulk_alert_notifications(db: Session, results: list):
    admin_users = db.query(User).filter(
        User.role.in_([Role.ADMIN, Role.FARMACIA])
    ).all()

    for result in results:
        if result.get("status") != "success":
            continue

        risk_level = result.get("risk_level", "low")
        if risk_level == "high":
            level = NotificationLevel.HIGH
        elif risk_level == "medium":
            level = NotificationLevel.MEDIUM
        else:
            continue

        med = db.get(Medication, result["medication_id"])
        if not med:
            continue

        for user in admin_users:
            notification = Notification(
                user_id=user.id,
                title=f"Alerta de desabastecimiento: {med.name}",
                message=f"El modelo predictivo indica un riesgo {risk_level} de desabastecimiento para '{med.name}'.",
                type=NotificationType.SHORTAGE_ALERT,
                level=level,
                related_entity_type="medication",
                related_entity_id=med.id
            )
            db.add(notification)
    db.commit()
