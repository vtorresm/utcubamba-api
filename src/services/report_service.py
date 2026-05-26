from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from src.models.report import (
    Report, ReportCreate, ReportUpdate, ReportStatus, ReportType
)
from src.models.user import User

logger = logging.getLogger(__name__)


def generate_report(
    db: Session,
    report_data: ReportCreate,
    user: User
) -> Report:
    report = Report(
        title=report_data.title,
        type=report_data.type,
        format=report_data.format,
        parameters=report_data.parameters or {},
        generated_by=user.id,
        status=ReportStatus.GENERATING,
        generated_at=datetime.utcnow()
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    try:
        data = _build_report_data(db, report.type, report.parameters or {})
        report.data = data
        report.status = ReportStatus.COMPLETED
        db.commit()
        db.refresh(report)
    except Exception as e:
        logger.error("Error generando reporte %s: %s", report.id, str(e), exc_info=True)
        report.status = ReportStatus.FAILED
        report.error_message = str(e)
        db.commit()
        db.refresh(report)

    return report


def _build_report_data(db: Session, report_type: ReportType, parameters: dict) -> dict:
    from src.models.medication import Medication
    from src.models.movement import Movement
    from src.models.prediction import Prediction

    if report_type == ReportType.INVENTORY:
        medications = db.query(Medication).all()
        return {
            "total_medications": len(medications),
            "medications": [
                {
                    "id": m.id,
                    "name": m.name,
                    "stock": m.stock,
                    "min_stock": m.min_stock,
                    "status": m.status
                }
                for m in medications
            ]
        }

    elif report_type == ReportType.MOVEMENTS:
        from sqlalchemy import func
        movements = db.query(
            Movement.type,
            func.count(Movement.id).label("count"),
            func.sum(Movement.quantity).label("total_quantity")
        ).group_by(Movement.type).all()
        return {
            "movements": [
                {"type": m.type, "count": m.count, "total_quantity": float(m.total_quantity)}
                for m in movements
            ],
            "period": parameters.get("period", "all")
        }

    elif report_type == ReportType.TRENDS:
        medications = db.query(Medication).all()
        trends = []
        for med in medications:
            predictions = db.query(Prediction).filter(
                Prediction.medication_id == med.id
            ).order_by(Prediction.date.desc()).limit(12).all()
            if predictions:
                trends.append({
                    "medication_id": med.id,
                    "medication_name": med.name,
                    "avg_predicted_usage": sum(p.predicted_usage for p in predictions) / len(predictions),
                    "trend": predictions[0].trend if predictions[0].trend else "stable"
                })
        return {"trends": trends}

    elif report_type == ReportType.ALERTS:
        alerts = db.query(Prediction).filter(
            Prediction.shortage == True
        ).order_by(Prediction.date.desc()).limit(100).all()
        return {
            "total_alerts": len(alerts),
            "alerts": [
                {
                    "medication_id": a.medication_id,
                    "probability": a.probability,
                    "alert_level": a.alert_level,
                    "date": a.date.isoformat()
                }
                for a in alerts
            ]
        }

    elif report_type == ReportType.FINANCIAL:
        from src.models.order import Order
        orders = db.query(Order).filter(
            Order.status == "received"
        ).all()
        total_cost = sum(o.total_cost for o in orders)
        return {
            "total_orders": len(orders),
            "total_cost": float(total_cost),
            "period": parameters.get("period", "all")
        }

    elif report_type == ReportType.PATIENTS:
        return {
            "message": "Reporte de pacientes: datos no disponibles actualmente",
            "period": parameters.get("period", "all")
        }

    return {"message": "Tipo de reporte no implementado"}


def get_reports(
    db: Session,
    user_id: Optional[int] = None,
    report_type: Optional[ReportType] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Report]:
    query = db.query(Report)
    if user_id is not None:
        query = query.filter(Report.generated_by == user_id)
    if report_type is not None:
        query = query.filter(Report.type == report_type)
    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


def get_report_by_id(db: Session, report_id: int) -> Optional[Report]:
    return db.get(Report, report_id)


def delete_report(db: Session, report_id: int) -> bool:
    report = db.get(Report, report_id)
    if not report:
        return False
    db.delete(report)
    db.commit()
    return True
