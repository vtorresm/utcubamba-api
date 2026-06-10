"""
Genera y persiste un forecast (ensemble ARIMA+Prophet) para cada medicamento,
de modo que el Dashboard y AI Insights muestren datos reales de inmediato.

Ejecutar desde el contenedor:
  docker compose exec -e PYTHONPATH=/app api python scripts/run_initial_forecasts.py
"""
from src.core.database import SessionLocal
from src.models.medication import Medication
from src.services.forecast_service import run_ensemble_forecast, save_forecast

db = SessionLocal()

try:
    meds = db.query(Medication).all()
    print(f"→ Generando forecasts para {len(meds)} medicamentos...\n")

    ok, failed = 0, 0
    for med in meds:
        try:
            result = run_ensemble_forecast(db, med.id, horizon_days=30, months_back=24)
            run = save_forecast(db, med.id, result)
            print(f"✓ {med.name:<28} alerta={run.alert_level:<8} "
                  f"días_hasta_desabasto={run.days_until_shortage}")
            ok += 1
        except Exception as e:
            print(f"❌ {med.name:<28} error: {e}")
            failed += 1

    print(f"\n✅ Completado: {ok} forecasts generados, {failed} fallidos.")
    print("Refresca el Dashboard y AI Insights para ver los datos.")

finally:
    db.close()
