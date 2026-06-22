"""
Re-ejecuta el forecast ensemble para todos los medicamentos activos.

Uso:
    docker compose exec api python scripts/rerun_forecasts.py

Limpia el cache joblib y recalcula todos los runs con WMAPE.
"""
import sys
import os
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import SessionLocal
from src.models.medication import Medication
from src.core.factory import ForecastModelFactory
from src.services.forecast_service import save_forecast

CACHE_DIR = os.environ.get("FORECAST_CACHE_DIR", "/tmp/forecast_models")


def clear_cache():
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR)
        print(f"  Cache limpiado: {CACHE_DIR}")
    else:
        print(f"  Cache no existia: {CACHE_DIR}")


def rerun_all(horizon_days=30, months_back=18):
    db = SessionLocal()
    fn = ForecastModelFactory.create("ensemble")

    try:
        # El seed usa "Activo" (no "active") — tomamos todos los medicamentos
        medications = db.query(Medication).all()
        print(f"\nMedicamentos encontrados: {len(medications)}\n")

        ok, fail = 0, 0

        for med in medications:
            try:
                result = fn(db, med.id, horizon_days, months_back)
                run = save_forecast(db, med.id, result)
                mape = result["metrics"].get("mape", "?")
                print(f"  OK  [{med.id:>3}] {med.name:<30}  WMAPE={mape:.1f}%  alerta={run.alert_level}")
                ok += 1
            except Exception as e:
                print(f"  ERR [{med.id:>3}] {med.name:<30}  {e}")
                fail += 1

        print(f"\nResumen: {ok} OK, {fail} errores")

    finally:
        db.close()


if __name__ == "__main__":
    print("=== Rerun Forecasts (WMAPE) ===\n")
    print("Limpiando cache joblib...")
    clear_cache()
    print("\nEjecutando forecasts ensemble...")
    rerun_all()
    print("\nListo. Recarga el dashboard para ver el WMAPE actualizado.")
