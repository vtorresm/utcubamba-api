from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
import io
import csv

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
        try:
            db.rollback()
            report.status = ReportStatus.FAILED
            report.error_message = str(e)[:999]
            db.commit()
            db.refresh(report)
        except Exception:
            db.rollback()

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
                {"type": m.type, "count": m.count, "total_quantity": float(m.total_quantity or 0)}
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
                "avg_predicted_usage": float(row.avg_predicted_usage or 0),
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


def _report_rows(report: Report):
    """Returns (headers, rows) for a report based on its type."""
    data = report.data or {}
    t = report.type

    if t == "inventory":
        headers = ["ID", "Nombre", "Stock", "Stock Mínimo", "Estado"]
        rows = [[m["id"], m["name"], m["stock"], m["min_stock"], m["status"]]
                for m in data.get("medications", [])]
    elif t == "movements":
        headers = ["Tipo", "Cantidad de movimientos", "Total unidades"]
        rows = [[m["type"], m["count"], m["total_quantity"]]
                for m in data.get("movements", [])]
    elif t == "trends":
        headers = ["Medicamento", "Uso promedio predicho", "Tendencia"]
        rows = [[r["medication_name"], round(r["avg_predicted_usage"], 2), r["trend"]]
                for r in data.get("trends", [])]
    elif t == "alerts":
        headers = ["Medicamento ID", "Probabilidad", "Nivel de alerta", "Fecha"]
        rows = [[a["medication_id"], f'{a["probability"]:.0%}', a["alert_level"], a["date"]]
                for a in data.get("alerts", [])]
    elif t == "financial":
        headers = ["Total órdenes", "Costo total (S/.)", "Período"]
        rows = [[data.get("total_orders", 0), data.get("total_cost", 0), data.get("period", "—")]]
    else:
        headers = ["Información"]
        rows = [[str(data)]]

    return headers, rows


def build_csv(report: Report) -> bytes:
    headers, rows = _report_rows(report)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")  # BOM para compatibilidad con Excel


def build_pdf(report: Report) -> bytes:
    from fpdf import FPDF

    headers, rows = _report_rows(report)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Título
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, report.title.encode("latin-1", "replace").decode("latin-1"), ln=True)

    # Metadata
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    generated = report.generated_at.strftime("%d/%m/%Y %H:%M") if report.generated_at else "—"
    pdf.cell(0, 6, f"Generado: {generated}  |  Tipo: {report.type}", ln=True)
    pdf.ln(4)

    # Tabla
    pdf.set_text_color(0, 0, 0)
    col_width = (pdf.w - 20) / max(len(headers), 1)

    # Headers
    pdf.set_fill_color(0, 87, 205)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for h in headers:
        pdf.cell(col_width, 8, str(h).encode("latin-1", "replace").decode("latin-1"), border=1, fill=True)
    pdf.ln()

    # Rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for i, row in enumerate(rows):
        if i % 2 == 0:
            pdf.set_fill_color(240, 244, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        for cell in row:
            pdf.cell(col_width, 7, str(cell).encode("latin-1", "replace").decode("latin-1"), border=1, fill=True)
        pdf.ln()

    return bytes(pdf.output())


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
