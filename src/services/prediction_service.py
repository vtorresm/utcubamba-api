"""
DEPRECADO - reemplazado por forecast_service.py.

La implementacion de Random Forest fue eliminada en favor de ARIMA y Prophet,
que proveen intervalos de confianza nativos y modelado explicito de
estacionalidad, necesarios para derivar la probabilidad estadistica de
desabastecimiento.

Este modulo mantiene stubs minimos para no romper imports existentes.
"""


def predict_shortage_risk(db, medication_id, days_ahead=30):
    """Stub - usar run_ensemble_forecast() de forecast_service."""
    raise NotImplementedError(
        "predict_shortage_risk fue eliminado. "
        "Usar run_ensemble_forecast() de forecast_service."
    )


def get_predictions(db, medication_id=None, skip=0, limit=100):
    """Stub - los datos estan en la tabla forecast_runs."""
    return []


def calculate_risk_level(probability):
    """Mapeo de probabilidad a nivel de alerta."""
    if probability >= 0.70:
        return "high"
    if probability >= 0.35:
        return "medium"
    return "low"


def calculate_days_until_shortage(stock, daily_avg):
    """Dias estimados hasta que el stock se agote."""
    if daily_avg <= 0:
        return None
    return int(stock / daily_avg)
