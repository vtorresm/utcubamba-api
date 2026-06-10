"""
Servicio de forecasting de consumo de medicamentos.

Implementa tres modelos de predicción de series de tiempo:
  - ARIMA   (Auto-ARIMA via pmdarima)
  - Prophet (Facebook / Meta Prophet)
  - Random Forest (sklearn, ya existente — usado como baseline)
  - Ensemble: promedio ponderado de los modelos disponibles

Flujo:
  1. get_consumption_series()  → agrega movimientos OUT por día
  2. run_*_forecast()          → entrena modelo y genera serie futura
  3. save_forecast()           → persiste ForecastRun + ForecastPoints en DB
  4. get_shortage_summary()    → resumen de riesgo por medicamento
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from sqlmodel import Session, select

from src.models.forecast import ForecastRun, ForecastPoint, ForecastRunCreate
from src.models.medication import Medication
from src.models.movement import Movement, MovementType

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Preparación de datos
# ─────────────────────────────────────────────────────────────────────────────

def get_consumption_series(
    db: Session,
    medication_id: int,
    months_back: int = 24,
    freq: str = "D",          # "D" daily, "W" weekly, "ME" month-end
) -> pd.Series:
    """
    Devuelve una Serie de Pandas con el consumo (movimientos OUT)
    del medicamento, indexada por fecha y rellenada con ceros.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months_back)

    stmt = select(Movement).where(
        Movement.medication_id == medication_id,
        Movement.type == MovementType.OUT,
        Movement.date >= start_date,
        Movement.date <= end_date,
    )
    movements = db.exec(stmt).all()

    if not movements:
        return pd.Series(dtype=float)

    df = pd.DataFrame([{"date": m.date.date(), "quantity": m.quantity} for m in movements])
    df["date"] = pd.to_datetime(df["date"])
    series = df.groupby("date")["quantity"].sum()

    # Completar fechas faltantes con 0
    full_idx = pd.date_range(start=series.index.min(), end=series.index.max(), freq="D")
    series = series.reindex(full_idx, fill_value=0.0)

    if freq != "D":
        series = series.resample(freq).sum()

    return series


def _eval_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """MAE, MAPE, RMSE, R²."""
    mae = float(np.mean(np.abs(y_true - y_pred)))
    mask = y_true != 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100) if mask.any() else 0.0
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    return {"mae": mae, "mape": mape, "rmse": rmse, "r2": r2}


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ARIMA
# ─────────────────────────────────────────────────────────────────────────────

def run_arima_forecast(
    db: Session,
    medication_id: int,
    horizon_days: int = 30,
    months_back: int = 18,
) -> dict:
    """
    Auto-ARIMA sobre la serie de consumo diario.
    Usa pmdarima.auto_arima para seleccionar automáticamente (p,d,q)(P,D,Q).
    """
    try:
        import pmdarima as pm
    except ImportError:
        raise RuntimeError("pmdarima no está instalado. Agrega 'pmdarima' a requirements.txt")

    series = get_consumption_series(db, medication_id, months_back=months_back, freq="D")
    if len(series) < 14:
        raise ValueError(f"Datos insuficientes para ARIMA: {len(series)} días (mínimo 14)")

    # Dividir en train/test (últimos 30 días como test si hay suficientes)
    test_size = min(30, len(series) // 5)
    train = series.iloc[:-test_size]
    test  = series.iloc[-test_size:]

    model = pm.auto_arima(
        train,
        seasonal=True,
        m=7,                  # estacionalidad semanal
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore",
        max_p=3, max_q=3, max_P=2, max_Q=2,
        information_criterion="aic",
    )

    # Evaluación sobre test
    test_pred, test_ci = model.predict(n_periods=test_size, return_conf_int=True)
    metrics = _eval_metrics(test.values, test_pred)

    # Re-entrenar con toda la serie para forecast final
    model.update(test)
    forecast_vals, forecast_ci = model.predict(
        n_periods=horizon_days, return_conf_int=True
    )
    forecast_vals = np.maximum(forecast_vals, 0)

    dates = pd.date_range(start=series.index[-1] + timedelta(days=1), periods=horizon_days, freq="D")

    return {
        "model_type": "arima",
        "parameters": {
            "order": list(model.order),
            "seasonal_order": list(model.seasonal_order),
            "aic": float(model.aic()),
        },
        "metrics": metrics,
        "dates": dates,
        "values": forecast_vals,
        "lower_ci": np.maximum(forecast_ci[:, 0], 0),
        "upper_ci": forecast_ci[:, 1],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Prophet
# ─────────────────────────────────────────────────────────────────────────────

def run_prophet_forecast(
    db: Session,
    medication_id: int,
    horizon_days: int = 30,
    months_back: int = 24,
) -> dict:
    """
    Facebook Prophet con estacionalidad semanal y anual.
    Robusto ante datos faltantes y cambios de tendencia.
    """
    try:
        from prophet import Prophet
    except ImportError:
        raise RuntimeError("prophet no está instalado. Agrega 'prophet' a requirements.txt")

    # Verificar que cmdstan esté disponible
    try:
        import cmdstanpy
        cmdstanpy.cmdstan_path()
    except Exception:
        raise RuntimeError(
            "cmdstan no está instalado. "
            "Usa el modelo 'arima' o ejecuta: docker compose up -d --build api"
        )

    series = get_consumption_series(db, medication_id, months_back=months_back, freq="D")
    if len(series) < 30:
        raise ValueError(f"Datos insuficientes para Prophet: {len(series)} días (mínimo 30)")

    # Prophet necesita columnas 'ds' y 'y'
    df_prophet = pd.DataFrame({"ds": series.index, "y": series.values})

    # Train/test split
    test_size = min(30, len(df_prophet) // 5)
    df_train = df_prophet.iloc[:-test_size]
    df_test  = df_prophet.iloc[-test_size:]

    try:
        model = Prophet(
            weekly_seasonality=True,
            yearly_seasonality=True if len(df_train) > 365 else False,
            daily_seasonality=False,
            seasonality_mode="multiplicative",
            interval_width=0.95,
        )
        model.fit(df_train)
    except AttributeError as e:
        raise RuntimeError(
            f"Incompatibilidad prophet/cmdstanpy ({e}). "
            "Reconstruye la imagen: docker compose up -d --build api"
        )

    # Eval sobre test
    future_test = model.make_future_dataframe(periods=test_size, include_history=False)
    fc_test = model.predict(future_test)
    test_pred = np.maximum(fc_test["yhat"].values, 0)
    metrics = _eval_metrics(df_test["y"].values, test_pred)

    # Re-fit con todos los datos
    model2 = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True if len(df_prophet) > 365 else False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        interval_width=0.95,
    )
    model2.fit(df_prophet)
    future = model2.make_future_dataframe(periods=horizon_days, include_history=False)
    forecast = model2.predict(future)

    dates = pd.DatetimeIndex(forecast["ds"])
    values = np.maximum(forecast["yhat"].values, 0)
    lower_ci = np.maximum(forecast["yhat_lower"].values, 0)
    upper_ci = forecast["yhat_upper"].values

    return {
        "model_type": "prophet",
        "parameters": {
            "seasonality_mode": "multiplicative",
            "weekly_seasonality": True,
            "yearly_seasonality": len(df_prophet) > 365,
        },
        "metrics": metrics,
        "dates": dates,
        "values": values,
        "lower_ci": lower_ci,
        "upper_ci": upper_ci,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Ensemble (promedio ponderado por 1/RMSE)
# ─────────────────────────────────────────────────────────────────────────────

def run_ensemble_forecast(
    db: Session,
    medication_id: int,
    horizon_days: int = 30,
    months_back: int = 24,
) -> dict:
    """
    Combina ARIMA y Prophet con pesos proporcionales a 1/RMSE.
    Si un modelo falla, se usa el otro individualmente.
    """
    results = {}
    errors  = {}

    for name, fn in [("arima", run_arima_forecast), ("prophet", run_prophet_forecast)]:
        try:
            results[name] = fn(db, medication_id, horizon_days, months_back)
        except Exception as e:
            errors[name] = str(e)
            logger.warning("Ensemble: %s falló — %s", name, e)

    if not results:
        raise ValueError(f"Todos los modelos fallaron: {errors}")

    # Calcular pesos por 1/RMSE
    rmse_vals = {k: v["metrics"]["rmse"] for k, v in results.items()}
    inv_rmse = {k: 1 / (v + 1e-9) for k, v in rmse_vals.items()}
    total = sum(inv_rmse.values())
    weights = {k: v / total for k, v in inv_rmse.items()}

    # Combinar series
    base_dates = list(results.values())[0]["dates"]
    combined_values   = np.zeros(horizon_days)
    combined_lower_ci = np.zeros(horizon_days)
    combined_upper_ci = np.zeros(horizon_days)

    for name, res in results.items():
        w = weights[name]
        combined_values   += w * res["values"]
        combined_lower_ci += w * res["lower_ci"]
        combined_upper_ci += w * res["upper_ci"]

    avg_metrics = {}
    for metric in ["mae", "mape", "rmse", "r2"]:
        avg_metrics[metric] = float(np.mean([r["metrics"][metric] for r in results.values()]))

    return {
        "model_type": "ensemble",
        "parameters": {
            "models_used": list(results.keys()),
            "weights": weights,
            "individual_rmse": rmse_vals,
        },
        "metrics": avg_metrics,
        "dates": base_dates,
        "values": combined_values,
        "lower_ci": combined_lower_ci,
        "upper_ci": combined_upper_ci,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Persistencia y helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_shortage_risk(
    medication: Medication,
    daily_avg: float,
    horizon_days: int,
) -> dict:
    """Calcula riesgo de desabastecimiento dado un consumo diario promedio."""
    if daily_avg <= 0:
        return {"days_until_shortage": None, "shortage_probability": 0.0, "alert_level": "low"}

    available = max(0.0, float(medication.stock) - float(medication.min_stock))
    days = int(available / daily_avg)

    if days <= 7:
        level = "high"
        prob  = 0.90
    elif days <= 14:
        level = "medium"
        prob  = 0.55
    elif days <= 30:
        level = "medium"
        prob  = 0.30
    else:
        level = "low"
        prob  = 0.05

    return {
        "days_until_shortage": days,
        "shortage_probability": prob,
        "alert_level": level,
    }


def save_forecast(db: Session, medication_id: int, forecast_data: dict) -> ForecastRun:
    """Persiste un ForecastRun con sus ForecastPoints en la base de datos."""
    medication = db.get(Medication, medication_id)
    if not medication:
        raise ValueError(f"Medicamento {medication_id} no encontrado")

    daily_avg = float(np.mean(forecast_data["values"]))
    horizon   = len(forecast_data["dates"])
    risk      = _compute_shortage_risk(medication, daily_avg, horizon)
    metrics   = forecast_data.get("metrics", {})

    run = ForecastRun(
        medication_id=medication_id,
        model_type=forecast_data["model_type"],
        horizon_days=horizon,
        mae=metrics.get("mae"),
        mape=metrics.get("mape"),
        rmse=metrics.get("rmse"),
        r2=metrics.get("r2"),
        parameters=forecast_data.get("parameters", {}),
        stock_at_forecast=float(medication.stock),
        days_until_shortage=risk["days_until_shortage"],
        shortage_probability=risk["shortage_probability"],
        alert_level=risk["alert_level"],
    )
    db.add(run)
    db.flush()  # obtener run.id sin commit

    for date, val, low, up in zip(
        forecast_data["dates"],
        forecast_data["values"],
        forecast_data["lower_ci"],
        forecast_data["upper_ci"],
    ):
        pt = ForecastPoint(
            forecast_run_id=run.id,
            date=pd.Timestamp(date).to_pydatetime(),
            predicted_value=max(0.0, float(val)),
            lower_ci=max(0.0, float(low)),
            upper_ci=max(0.0, float(up)),
        )
        db.add(pt)

    db.commit()
    db.refresh(run)
    return run


def get_forecast_summary(db: Session) -> list[dict]:
    """
    Resumen de desabastecimiento para todos los medicamentos,
    usando el ForecastRun más reciente de cada uno.
    """
    medications = db.exec(select(Medication)).all()
    summary = []
    for med in medications:
        latest = (
            db.exec(
                select(ForecastRun)
                .where(ForecastRun.medication_id == med.id)
                .order_by(ForecastRun.created_at.desc())
            ).first()
        )
        summary.append({
            "medication_id": med.id,
            "medication_name": med.name,
            "stock": med.stock,
            "min_stock": med.min_stock,
            "alert_level": latest.alert_level if latest else None,
            "days_until_shortage": latest.days_until_shortage if latest else None,
            "shortage_probability": latest.shortage_probability if latest else None,
            "last_forecast": latest.created_at.isoformat() if latest else None,
            "model_type": latest.model_type if latest else None,
        })
    return summary
