"""
Genera movimientos de consumo DIARIO realistas para todos los medicamentos.

Reemplaza los movimientos mensuales del seed_db.py con datos diarios que
tienen estacionalidad semanal + anual + ruido bajo, permitiendo que
ARIMA/Prophet aprendan patrones y alcancen WMAPE < 15%.

Uso:
    docker compose exec api python scripts/seed_daily_movements.py
"""
import sys
import os
import random
import math
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sqlmodel import Session, select
from src.core.database import engine
from src.models.medication import Medication
from src.models.movement import Movement, MovementType

# Seed para reproducibilidad
random.seed(2024)
np.random.seed(2024)

# Consumo base diario por categoria (unidades/dia)
BASE_DAILY = {
    "Analgesico":      4.5,
    "Antibiotico":     2.8,
    "Cardiovascular":  3.2,
    "Diabetes":        2.5,
    "Respiratorio":    3.0,
    "Alergia":         2.0,
    "default":         3.0,
}

# Factor semanal (lunes=0 ... domingo=6)
# Hospitales tienen mas consumo entre semana
WEEKLY_FACTOR = [1.15, 1.10, 1.05, 1.05, 1.10, 0.85, 0.70]

# Factor mensual por categoria (indice 0=enero ... 11=diciembre)
MONTHLY_FACTOR = {
    "Analgesico":   [1.3, 1.3, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.3],
    "Antibiotico":  [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.3, 1.2, 1.0],
    "Cardiovascular":[1.0]*12,
    "Diabetes":     [1.0]*12,
    "Respiratorio": [1.3, 1.2, 1.1, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2],
    "Alergia":      [1.0, 1.0, 1.2, 1.4, 1.3, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    "default":      [1.0]*12,
}


def get_category_name(medication: Medication, db: Session) -> str:
    if medication.category_id is None:
        return "default"
    from src.models.category import Category
    cat = db.get(Category, medication.category_id)
    if cat is None:
        return "default"
    name = cat.name.strip()
    for key in BASE_DAILY:
        if key.lower() in name.lower():
            return key
    return "default"


def generate_daily_series(
    base: float,
    weekly: list,
    monthly: list,
    days: int = 730,
    noise_cv: float = 0.18,
) -> list[float]:
    """
    Genera serie diaria con:
    - Estacionalidad semanal (dias de la semana)
    - Estacionalidad anual (meses del ano)
    - Ruido gaussiano bajo (CV ~18%)
    - Trend ligero ascendente (1% acumulado por ano)
    """
    series = []
    start = datetime.utcnow() - timedelta(days=days)
    for d in range(days):
        date = start + timedelta(days=d)
        dow = date.weekday()          # 0=lunes
        month = date.month - 1        # 0=enero

        trend = 1.0 + 0.01 * (d / 365)
        w = weekly[dow]
        m = monthly[month]
        noise = np.random.normal(1.0, noise_cv)
        noise = max(0.2, noise)       # no negativos

        val = base * w * m * trend * noise
        series.append(max(0.0, round(val, 2)))
    return series


def seed_movements(db: Session):
    medications = db.exec(select(Medication)).all()
    print(f"Medicamentos: {len(medications)}")

    # Empezar desde ene 2025 para no solapar con el seed mensual (que termina dic 2024)
    # Esto da ~18 meses de datos diarios hasta hoy
    start_date = datetime(2025, 1, 1)
    end_date = datetime.utcnow()
    days = (end_date - start_date).days

    print(f"Generando {days} dias de datos diarios ({start_date.date()} -> {end_date.date()})\n")

    total_created = 0

    for med in medications:
        cat = get_category_name(med, db)
        base = BASE_DAILY.get(cat, BASE_DAILY["default"])
        base *= random.uniform(0.8, 1.2)

        weekly = WEEKLY_FACTOR
        monthly = MONTHLY_FACTOR.get(cat, MONTHLY_FACTOR["default"])

        series = generate_daily_series(base, weekly, monthly, days=days)

        # Solo insertar si no existen movimientos diarios en este periodo
        existing_count = len(db.exec(
            select(Movement).where(
                Movement.medication_id == med.id,
                Movement.type == MovementType.OUT,
                Movement.date >= start_date,
            )
        ).all())

        if existing_count > 100:
            print(f"  SKIP [{med.id:>3}] {med.name:<28} ya tiene {existing_count} movimientos diarios")
            continue

        date = start_date
        created = 0
        for qty in series:
            if qty > 0.05:
                mv = Movement(
                    medication_id=med.id,
                    date=date,
                    type=MovementType.OUT,
                    quantity=round(qty, 2),
                )
                db.add(mv)
                created += 1
            date += timedelta(days=1)

        db.commit()
        print(f"  OK  [{med.id:>3}] {med.name:<28} cat={cat:<14} base={base:.2f}  dias={created}")
        total_created += created

    print(f"\nTotal movimientos creados: {total_created}")


if __name__ == "__main__":
    print("=== Seed Movimientos Diarios ===\n")
    with Session(engine) as db:
        seed_movements(db)
    print("\nListo. Ejecuta ahora: python scripts/rerun_forecasts.py")
