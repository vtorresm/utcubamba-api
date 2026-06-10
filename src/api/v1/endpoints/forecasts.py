"""
Endpoints de forecasting de desabastecimiento de medicamentos.

GET  /forecasts/{medication_id}          — ejecuta forecast y devuelve serie
GET  /forecasts/{medication_id}/history  — historial de runs para un medicamento
GET  /forecasts/summary                  — resumen de riesgo para todos los meds
DELETE /forecasts/{run_id}               — borra un run (solo admin)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import pandas as pd

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.user import User
from src.models.medication import Medication
from src.models.forecast import ForecastRun, ForecastPoint, ForecastFullResponse
from src.services.forecast_service import (
    run_arima_forecast,
    run_prophet_forecast,
    run_ensemble_forecast,
    save_forecast,
    get_forecast_summary,
)

logger = logging.getLogger(__name__)
router = APIRouter()

MODEL_FNS = {
    "arima":   run_arima_forecast,
    "prophet": run_prophet_forecast,
    "ensemble": run_ensemble_forecast,
}


# ─────────────────────────────────────────────────────────────────────────────
# POST — ejecutar forecast
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{medication_id}",
    response_model=Dict[str, Any],
    summary="Ejecutar forecast de desabastecimiento",
    tags=["forecasts"],
    responses={
        200: {"description": "Forecast generado y persistido"},
        404: {"description": "Medicamento no encontrado"},
        422: {"description": "Datos insuficientes para el modelo"},
    },
)
async def run_forecast(
    medication_id: int = Path(..., gt=0),
    model: str = Query(
        default="ensemble",
        description="Modelo a usar: 'arima', 'prophet', 'ensemble'",
    ),
    horizon_days: int = Query(default=30, ge=7, le=180),
    months_back: int = Query(default=24, ge=6, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:

    # Verificar medicamento
    medication = db.get(Medication, medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail=f"Medicamento {medication_id} no encontrado")

    if model not in MODEL_FNS:
        raise HTTPException(
            status_code=422,
            detail=f"Modelo '{model}' no válido. Opciones: {list(MODEL_FNS.keys())}",
        )

    try:
        fn = MODEL_FNS[model]
        result = fn(db, medication_id, horizon_days, months_back)
        run = save_forecast(db, medication_id, result)

        # Construir respuesta
        points = [
            {
                "date": pd.Timestamp(d).strftime("%Y-%m-%d"),
                "predicted_value": round(float(v), 2),
                "lower_ci": round(float(l), 2),
                "upper_ci": round(float(u), 2),
            }
            for d, v, l, u in zip(
                result["dates"],
                result["values"],
                result["lower_ci"],
                result["upper_ci"],
            )
        ]

        return {
            "run_id": run.id,
            "medication_id": medication_id,
            "medication_name": medication.name,
            "model_type": model,
            "horizon_days": horizon_days,
            "metrics": result["metrics"],
            "parameters": result.get("parameters", {}),
            "stock_at_forecast": run.stock_at_forecast,
            "days_until_shortage": run.days_until_shortage,
            "shortage_probability": run.shortage_probability,
            "alert_level": run.alert_level,
            "created_at": run.created_at.isoformat(),
            "points": points,
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Error en run_forecast: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "forecast_failed", "message": str(e)},
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET — historial de runs para un medicamento
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{medication_id}/history",
    response_model=Dict[str, Any],
    summary="Historial de forecasts para un medicamento",
    tags=["forecasts"],
)
async def get_forecast_history(
    medication_id: int = Path(..., gt=0),
    limit: int = Query(default=10, ge=1, le=50),
    model: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:

    from sqlmodel import select

    medication = db.get(Medication, medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail=f"Medicamento {medication_id} no encontrado")

    stmt = (
        select(ForecastRun)
        .where(ForecastRun.medication_id == medication_id)
        .order_by(ForecastRun.created_at.desc())
        .limit(limit)
    )
    if model:
        stmt = stmt.where(ForecastRun.model_type == model)

    runs = db.exec(stmt).all()

    return {
        "medication_id": medication_id,
        "medication_name": medication.name,
        "total": len(runs),
        "runs": [
            {
                "run_id": r.id,
                "model_type": r.model_type,
                "horizon_days": r.horizon_days,
                "mae": r.mae,
                "mape": r.mape,
                "rmse": r.rmse,
                "alert_level": r.alert_level,
                "days_until_shortage": r.days_until_shortage,
                "shortage_probability": r.shortage_probability,
                "created_at": r.created_at.isoformat(),
            }
            for r in runs
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET — último forecast con puntos para un medicamento
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{medication_id}/latest",
    response_model=Dict[str, Any],
    summary="Último forecast con puntos para un medicamento",
    tags=["forecasts"],
)
async def get_latest_forecast(
    medication_id: int = Path(..., gt=0),
    model: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:

    from sqlmodel import select

    medication = db.get(Medication, medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail=f"Medicamento {medication_id} no encontrado")

    stmt = (
        select(ForecastRun)
        .where(ForecastRun.medication_id == medication_id)
        .order_by(ForecastRun.created_at.desc())
    )
    if model:
        stmt = stmt.where(ForecastRun.model_type == model)

    run = db.exec(stmt).first()
    if not run:
        raise HTTPException(
            status_code=404,
            detail="No hay forecasts previos para este medicamento. Ejecuta POST primero.",
        )

    points_stmt = (
        select(ForecastPoint)
        .where(ForecastPoint.forecast_run_id == run.id)
        .order_by(ForecastPoint.date)
    )
    points = db.exec(points_stmt).all()

    return {
        "run_id": run.id,
        "medication_id": medication_id,
        "medication_name": medication.name,
        "model_type": run.model_type,
        "horizon_days": run.horizon_days,
        "mae": run.mae,
        "mape": run.mape,
        "rmse": run.rmse,
        "r2": run.r2,
        "alert_level": run.alert_level,
        "days_until_shortage": run.days_until_shortage,
        "shortage_probability": run.shortage_probability,
        "stock_at_forecast": run.stock_at_forecast,
        "parameters": run.parameters,
        "created_at": run.created_at.isoformat(),
        "points": [
            {
                "date": pt.date.strftime("%Y-%m-%d"),
                "predicted_value": round(pt.predicted_value, 2),
                "lower_ci": round(pt.lower_ci or 0, 2),
                "upper_ci": round(pt.upper_ci or 0, 2),
            }
            for pt in points
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET — resumen de riesgo para todos los medicamentos
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Resumen de riesgo de desabastecimiento para todos los medicamentos",
    tags=["forecasts"],
)
async def forecast_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:

    summary = get_forecast_summary(db)
    high   = [s for s in summary if s["alert_level"] == "high"]
    medium = [s for s in summary if s["alert_level"] == "medium"]
    low    = [s for s in summary if s["alert_level"] == "low"]

    return {
        "total_medications": len(summary),
        "high_risk": len(high),
        "medium_risk": len(medium),
        "low_risk": len(low),
        "no_forecast": len([s for s in summary if s["alert_level"] is None]),
        "medications": summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DELETE — borrar un run (solo admin)
# ─────────────────────────────────────────────────────────────────────────────

@router.delete(
    "/run/{run_id}",
    status_code=204,
    summary="Eliminar un forecast run",
    tags=["forecasts"],
)
async def delete_forecast_run(
    run_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from src.models.user import Role
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores")

    run = db.get(ForecastRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")

    db.delete(run)
    db.commit()
    return None


