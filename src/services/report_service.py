from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from src.models.report import (
    Report, ReportCreate, ReportStatus, ReportType
)
from src.models.user import User
from src.exceptions import ReportNotFoundError, ValidationError

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
    try:
        db.commit()
        db.refresh(report)
    except Exception:
        db.rollback()
        raise

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
        from sqlalchemy import text
        stmt = text("""
            SELECT
                p.medication_id,
                m.name AS medication_name,
                AVG(p.predicted_usage) AS avg_predicted_usage,
                p.trend
            FROM predictions p
            JOIN medications m ON m.id = p.medication_id
            WHERE p.id IN (
                SELECT id FROM (
                    SELECT id, medication_id,
                        ROW_NUMBER() OVER (PARTITION BY medication_id ORDER BY date DESC) AS rn
                    FROM predictions
                ) sub WHERE rn <= 12
            )
            GROUP BY p.medication_id, m.name, p.trend
        """)
        rows = db.execute(stmt).fetchall()
        trends = [
            {
                "medication_id": row.medication_id,
                "medication_name": row.medication_name,
                "avg_predicted_usage": float(row.avg_predicted_usage),
                "trend": row.trend or "stable"
            }
            for row in rows
        ]
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
        result = db.query(
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total_cost).label("total_cost")
        ).filter(Order.status == "received").first()
        return {
            "total_orders": result.total_orders or 0,
            "total_cost": float(result.total_cost or 0),
            "period": parameters.get("period", "all")
        }

    elif report_type == ReportType.PATIENTS:
        return {
            "message": "Reporte de pacientes: datos no disponibles actualmente",
            "period": parameters.get("period", "all")
        }

    raise ValidationError(f"Tipo de reporte no implementado: {report_type}")


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


def get_report_by_id(db: Session, report_id: int) -> Report:
    report = db.get(Report, report_id)
    if not report:
        raise ReportNotFoundError(report_id)
    return report


def delete_report(db: Session, report_id: int) -> None:
    report = db.get(Report, report_id)
    if not report:
        raise ReportNotFoundError(report_id)
    db.delete(report)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
