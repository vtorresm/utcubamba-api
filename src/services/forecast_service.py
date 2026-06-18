"""
Servicio de forecasting de consumo de medicamentos.

Modelos: ARIMA (pmdarima), Prophet (Facebook), Ensemble (1/RMSE ponderado).

Mejoras academicas implementadas
---------------------------------
1. Validacion Walk-forward (expanding window, 5 folds) reemplaza holdout estatico.
2. Probabilidad estadistica de desabastecimiento via scipy.stats.norm desde IC 95%.
3. Diagnostico Prophet: cross_validation() + performance_metrics() oficiales.
4. Persistencia de modelos con joblib (clave = hash MD5 de la serie).
5. Patron Repository: MovementRepository y ForecastRepository encapsulan la BD.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
from scipy.stats import norm
from sqlmodel import Session, select

from src.models.forecast import ForecastPoint, ForecastRun
from src.models.medication import Medication
from src.repositories import ForecastRepository, MovementRepository

logger = logging.getLogger(__name__)

_MODEL_CACHE_DIR = os.environ.get("FORECAST_CACHE_DIR", "/tmp/forecast_models")
os.makedirs(_MODEL_CACHE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Utilidades de serie de tiempo
# ---------------------------------------------------------------------------

def get_consumption_series(db, medication_id, months_back=24, freq="D"):
    """Devuelve la serie de consumo diario via MovementRepository."""
    repo = MovementRepository(db)
    return repo.get_consumption_series(medication_id, months_back=months_back, freq=freq)


def _series_hash(series):
    raw = ",".join(f"{v:.4f}" for v in series.values)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _cache_path(medication_id, model_type, series_hash):
    return os.path.join(_MODEL_CACHE_DIR, f"{model_type}_med{medication_id}_{series_hash}.joblib")


# ---------------------------------------------------------------------------
# 2. Metricas
# ---------------------------------------------------------------------------

def _eval_metrics(y_true, y_pred):
    mae = float(np.mean(np.abs(y_true - y_pred)))
    mask = y_true != 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100) if mask.any() else 0.0
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    return {"mae": mae, "mape": mape, "rmse": rmse, "r2": r2}


def _walk_forward_metrics(series, fit_fn, n_splits=5, test_window=14):
    """
    Validacion walk-forward (expanding window).

    Para cada fold k: train = serie[:N - k*test_window], test = siguientes test_window puntos.
    Promedia las metricas de todos los folds exitosos.

    Parameters
    ----------
    fit_fn : callable(train: pd.Series, n_periods: int) -> np.ndarray
    """
    min_train = max(30, len(series) // 3)
    all_metrics = []

    for k in range(n_splits, 0, -1):
        test_end = len(series) - (k - 1) * test_window
        test_start = test_end - test_window
        if test_start < min_train:
            continue
        train = series.iloc[:test_start]
        test = series.iloc[test_start:test_end]
        try:
            preds = np.maximum(fit_fn(train, len(test)), 0)
            all_metrics.append(_eval_metrics(test.values, preds))
        except Exception as e:
            logger.debug("Walk-forward fold %d fallo: %s", k, e)

    if not all_metrics:
        return {"mae": 0.0, "mape": 0.0, "rmse": 0.0, "r2": 0.0, "n_folds": 0}

    avg = {m: float(np.mean([x[m] for x in all_metrics])) for m in ("mae", "mape", "rmse", "r2")}
    avg["n_folds"] = len(all_metrics)
    return avg


# ---------------------------------------------------------------------------
# 3. ARIMA
# ---------------------------------------------------------------------------

def run_arima_forecast(db, medication_id, horizon_days=30, months_back=18):
    """
    Auto-ARIMA con walk-forward validation (5 folds) y persistencia joblib.

    Selecciona (p,d,q)(P,D,Q) minimizando AIC, estacionalidad semanal m=7.
    El modelo se serializa con joblib usando el hash de la serie como clave.
    """
    try:
        import pmdarima as pm
    except ImportError:
        raise RuntimeError("pmdarima no instalado.")

    series = get_consumption_series(db, medication_id, months_back=months_back, freq="D")
    if len(series) < 14:
        raise ValueError(f"Datos insuficientes para ARIMA: {len(series)} dias (minimo 14)")

    s_hash = _series_hash(series)
    cache = _cache_path(medication_id, "arima", s_hash)

    model = None
    if os.path.exists(cache):
        try:
            model = joblib.load(cache)
            logger.info("ARIMA cargado desde cache: %s", cache)
        except Exception:
            model = None

    def _arima_fit_predict(train, n_periods):
        m = pm.auto_arima(
            train, seasonal=True, m=7, stepwise=True,
            suppress_warnings=True, error_action="ignore",
            max_p=3, max_q=3, max_P=2, max_Q=2,
            information_criterion="aic",
        )
        preds, _ = m.predict(n_periods=n_periods, return_conf_int=True)
        return preds

    wf_metrics = _walk_forward_metrics(series, _arima_fit_predict, n_splits=5, test_window=14)
    wf_metrics["validation"] = "walk_forward_5_folds"

    if model is None:
        model = pm.auto_arima(
            series, seasonal=True, m=7, stepwise=True,
            suppress_warnings=True, error_action="ignore",
            max_p=3, max_q=3, max_P=2, max_Q=2,
            information_criterion="aic",
        )
        try:
            joblib.dump(model, cache)
        except Exception as e:
            logger.warning("No se pudo guardar cache ARIMA: %s", e)

    forecast_vals, forecast_ci = model.predict(n_periods=horizon_days, return_conf_int=True)
    forecast_vals = np.maximum(forecast_vals, 0)
    dates = pd.date_range(start=series.index[-1] + timedelta(days=1), periods=horizon_days, freq="D")

    return {
        "model_type": "arima",
        "parameters": {
            "order": list(model.order),
            "seasonal_order": list(model.seasonal_order),
            "aic": float(model.aic()),
            "validation": "walk_forward_5_folds",
        },
        "metrics": wf_metrics,
        "dates": dates,
        "values": forecast_vals,
        "lower_ci": np.maximum(forecast_ci[:, 0], 0),
        "upper_ci": forecast_ci[:, 1],
    }


# ---------------------------------------------------------------------------
# 4. Prophet
# ---------------------------------------------------------------------------

def run_prophet_forecast(db, medication_id, horizon_days=30, months_back=24):
    """
    Facebook Prophet con diagnostico oficial (cross_validation) y persistencia joblib.

    Usa estacionalidad multiplicativa. La validacion usa cross_validation() de
    prophet.diagnostics, que implementa walk-forward con ventana deslizante.
    """
    try:
        from prophet import Prophet
        from prophet.diagnostics import cross_validation, performance_metrics
    except ImportError:
        raise RuntimeError("prophet no instalado.")

    try:
        import cmdstanpy
        cmdstanpy.cmdstan_path()
    except Exception:
        raise RuntimeError("cmdstan no disponible. Usa 'arima' o reconstruye la imagen Docker.")

    series = get_consumption_series(db, medication_id, months_back=months_back, freq="D")
    if len(series) < 30:
        raise ValueError(f"Datos insuficientes para Prophet: {len(series)} dias (minimo 30)")

    df_prophet = pd.DataFrame({"ds": series.index, "y": series.values})
    yearly = len(df_prophet) > 365

    s_hash = _series_hash(series)
    cache = _cache_path(medication_id, "prophet", s_hash)

    model_final = None
    if os.path.exists(cache):
        try:
            model_final = joblib.load(cache)
            logger.info("Prophet cargado desde cache: %s", cache)
        except Exception:
            model_final = None

    # Diagnostico via prophet.diagnostics
    diag_metrics = {}
    if len(df_prophet) >= 90:
        try:
            _m_diag = Prophet(
                weekly_seasonality=True, yearly_seasonality=yearly,
                daily_seasonality=False, seasonality_mode="multiplicative",
                interval_width=0.95,
            )
            _m_diag.fit(df_prophet)
            n = len(df_prophet)
            initial_days = max(60, int(n * 0.60))
            period_days = max(14, int(n * 0.10))
            horizon_cv = f"{min(horizon_days, 30)} days"
            df_cv = cross_validation(
                _m_diag,
                initial=f"{initial_days} days",
                period=f"{period_days} days",
                horizon=horizon_cv,
                parallel=None,
            )
            df_perf = performance_metrics(df_cv, rolling_window=1)
            diag_metrics = {
                "mae": float(df_perf["mae"].mean()),
                "rmse": float(df_perf["rmse"].mean()),
                "mape": float(df_perf["mape"].mean() * 100),
                "r2": 0.0,
                "n_folds": int(df_cv["cutoff"].nunique()),
                "validation": "prophet_cross_validation",
            }
        except Exception as e:
            logger.warning("Prophet cross_validation fallo: %s", e)

    # Fallback walk-forward si CV fallo
    if not diag_metrics:
        def _prophet_fit_predict(train, n_periods):
            df_t = pd.DataFrame({"ds": train.index, "y": train.values})
            m = Prophet(
                weekly_seasonality=True, yearly_seasonality=len(df_t) > 365,
                daily_seasonality=False, seasonality_mode="multiplicative",
                interval_width=0.95,
            )
            m.fit(df_t)
            fut = m.make_future_dataframe(periods=n_periods, include_history=False)
            fc = m.predict(fut)
            return np.maximum(fc["yhat"].values, 0)

        wf = _walk_forward_metrics(series, _prophet_fit_predict, n_splits=3, test_window=14)
        diag_metrics = {**wf, "validation": "walk_forward_3_folds"}

    # Modelo final sobre toda la serie
    if model_final is None:
        try:
            model_final = Prophet(
                weekly_seasonality=True, yearly_seasonality=yearly,
                daily_seasonality=False, seasonality_mode="multiplicative",
                interval_width=0.95,
            )
            model_final.fit(df_prophet)
            try:
                joblib.dump(model_final, cache)
            except Exception as e:
                logger.warning("No se pudo guardar cache Prophet: %s", e)
        except AttributeError as e:
            raise RuntimeError(f"Incompatibilidad prophet/cmdstanpy ({e}).")

    future = model_final.make_future_dataframe(periods=horizon_days, include_history=False)
    forecast = model_final.predict(future)

    return {
        "model_type": "prophet",
        "parameters": {
            "seasonality_mode": "multiplicative",
            "weekly_seasonality": True,
            "yearly_seasonality": yearly,
            "interval_width": 0.95,
        },
        "metrics": diag_metrics,
        "dates": pd.DatetimeIndex(forecast["ds"]),
        "values": np.maximum(forecast["yhat"].values, 0),
        "lower_ci": np.maximum(forecast["yhat_lower"].values, 0),
        "upper_ci": forecast["yhat_upper"].values,
    }


# ---------------------------------------------------------------------------
# 5. Ensemble
# ---------------------------------------------------------------------------

def run_ensemble_forecast(db, medication_id, horizon_days=30, months_back=24):
    """
    Combina ARIMA y Prophet con pesos proporcionales a 1/RMSE.
    Degrada gracefully si un modelo falla.
    """
    results = {}
    errors = {}

    for name, fn in [("arima", run_arima_forecast), ("prophet", run_prophet_forecast)]:
        try:
            results[name] = fn(db, medication_id, horizon_days, months_back)
        except Exception as e:
            errors[name] = str(e)
            logger.warning("Ensemble: %s fallo - %s", name, e)

    if not results:
        raise ValueError(f"Todos los modelos fallaron: {errors}")

    rmse_vals = {k: v["metrics"]["rmse"] for k, v in results.items()}
    inv_rmse = {k: 1.0 / (v + 1e-9) for k, v in rmse_vals.items()}
    total = sum(inv_rmse.values())
    weights = {k: v / total for k, v in inv_rmse.items()}

    base_dates = list(results.values())[0]["dates"]
    combined_values = np.zeros(horizon_days)
    combined_lower = np.zeros(horizon_days)
    combined_upper = np.zeros(horizon_days)

    for name, res in results.items():
        w = weights[name]
        combined_values += w * res["values"]
        combined_lower  += w * res["lower_ci"]
        combined_upper  += w * res["upper_ci"]

    avg_metrics = {
        m: float(np.mean([r["metrics"][m] for r in results.values()]))
        for m in ("mae", "mape", "rmse", "r2")
    }

    return {
        "model_type": "ensemble",
        "parameters": {
            "models_used": list(results.keys()),
            "weights": weights,
            "individual_rmse": rmse_vals,
            "validation": "walk_forward_per_model",
        },
        "metrics": avg_metrics,
        "dates": base_dates,
        "values": combined_values,
        "lower_ci": combined_lower,
        "upper_ci": combined_upper,
    }


# ---------------------------------------------------------------------------
# 6. Probabilidad estadistica de desabastecimiento
# ---------------------------------------------------------------------------

def _compute_shortage_probability(medication, forecast_values, lower_ci, upper_ci):
    """
    Probabilidad de desabastecimiento derivada estadisticamente del IC 95%.

    Metodologia
    -----------
    IC 95% del modelo: [lower, upper] = mu +/- 1.96 * sigma_diario
      => sigma_diario = (upper - lower) / 3.92

    Consumo acumulado en H dias (por TCL):
      C_total ~ N(mu_total, sigma_total^2)
      mu_total    = sum(forecast_values)
      sigma_total = sqrt(sum(sigma_diario^2))

    P(desabasto) = P(C_total > stock_disponible)
                 = 1 - Phi((stock - mu_total) / sigma_total)
    con Phi = CDF de la normal estandar (scipy.stats.norm).
    """
    available = max(0.0, float(medication.stock) - float(medication.min_stock))

    sigma_daily = (upper_ci - lower_ci) / (2.0 * 1.96)
    sigma_daily = np.maximum(sigma_daily, 1e-9)

    cum_mean = float(np.sum(forecast_values))
    cum_std = float(np.sqrt(np.sum(sigma_daily ** 2)))

    if cum_std < 1e-6:
        prob = 1.0 if cum_mean > available else 0.0
    else:
        prob = float(1.0 - norm.cdf(available, loc=cum_mean, scale=cum_std))

    prob = float(np.clip(prob, 0.0, 1.0))

    cumsum = np.cumsum(forecast_values)
    arr = np.where(cumsum >= available)[0]
    days_until = int(arr[0]) + 1 if len(arr) > 0 else None

    if prob >= 0.70:
        level = "high"
    elif prob >= 0.35:
        level = "medium"
    else:
        level = "low"

    return {
        "days_until_shortage": days_until,
        "shortage_probability": round(prob, 4),
        "alert_level": level,
    }


# ---------------------------------------------------------------------------
# 7. Persistencia en BD
# ---------------------------------------------------------------------------

def save_forecast(db, medication_id, forecast_data):
    """
    Persiste ForecastRun + ForecastPoints usando ForecastRepository.
    La probabilidad de desabastecimiento se deriva del IC (estadisticamente).
    """
    medication = db.get(Medication, medication_id)
    if not medication:
        raise ValueError(f"Medicamento {medication_id} no encontrado")

    risk = _compute_shortage_probability(
        medication, forecast_data["values"], forecast_data["lower_ci"], forecast_data["upper_ci"]
    )
    metrics = forecast_data.get("metrics", {})
    horizon = len(forecast_data["dates"])

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

    points = [
        ForecastPoint(
            forecast_run_id=0,
            date=pd.Timestamp(date).to_pydatetime(),
            predicted_value=max(0.0, float(val)),
            lower_ci=max(0.0, float(low)),
            upper_ci=max(0.0, float(up)),
        )
        for date, val, low, up in zip(
            forecast_data["dates"], forecast_data["values"],
            forecast_data["lower_ci"], forecast_data["upper_ci"],
        )
    ]

    repo = ForecastRepository(db)
    return repo.save_run_with_points(run, points)


def get_forecast_summary(db):
    """Resumen de riesgo de desabastecimiento para todos los medicamentos."""
    medications = db.exec(select(Medication)).all()
    forecast_repo = ForecastRepository(db)
    summary = []
    for med in medications:
        latest = forecast_repo.get_latest_for_medication(med.id)
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
