"""
Script para sembrar medicamentos de ejemplo en la base de datos.
Ejecutar desde el contenedor:
  docker compose exec api python scripts/seed_medications.py
"""
from src.core.database import SessionLocal
from src.models.medication import Medication
from src.models.category import Category
from src.models.movement import Movement, MovementType
from datetime import datetime, timedelta
import random

db = SessionLocal()

try:
    # ── Categorías ──────────────────────────────────────────────────────────
    cats_data = [
        ("Analgésico",   "Medicamentos para el dolor"),
        ("Antibiótico",  "Antibióticos de amplio espectro"),
        ("Alergia",      "Antihistamínicos y antialérgicos"),
        ("Diabetes",     "Tratamiento de diabetes"),
        ("Respiratorio", "Broncodilatadores e inhaladores"),
        ("Cardiovascular","Medicamentos para el corazón"),
    ]
    cats = {}
    for name, desc in cats_data:
        c = db.query(Category).filter(Category.name == name).first()
        if not c:
            c = Category(name=name, description=desc)
            db.add(c)
            db.flush()
        cats[name] = c
    db.commit()
    print(f"✓ {len(cats)} categorías")

    # ── Medicamentos ────────────────────────────────────────────────────────
    meds_data = [
        ("Ibuprofeno 400mg",        "Analgésico",    450, 80,  "Tabletas", 0.04,  90),
        ("Amoxicilina 500mg",       "Antibiótico",   380, 100, "Cápsulas", 0.08,  120),
        ("Loratadina 10mg",         "Alergia",       55,  60,  "Tabletas", 0.12,  45),
        ("Insulina Glargina 100UI", "Diabetes",      20,  30,  "Viales",   42.50, 15),
        ("Salbutamol Inhalador",    "Respiratorio",  95,  40,  "Frascos",  8.90,  60),
        ("Metformina 850mg",        "Diabetes",      310, 80,  "Tabletas", 0.06,  90),
        ("Paracetamol 500mg",       "Analgésico",    8,   200, "Tabletas", 0.03,  200),
        ("Atorvastatina 20mg",      "Cardiovascular",180, 50,  "Tabletas", 0.15,  60),
        ("Azitromicina 500mg",      "Antibiótico",   72,  40,  "Tabletas", 0.45,  30),
        ("Enalapril 10mg",          "Cardiovascular",250, 60,  "Tabletas", 0.08,  90),
    ]

    created_meds = []
    for name, cat_name, stock, min_stock, unit, price, days_expiry in meds_data:
        m = db.query(Medication).filter(Medication.name == name).first()
        if not m:
            m = Medication(
                name=name,
                stock=stock,
                min_stock=min_stock,
                unit=unit,
                price=price,
                status="Activo",
                category_id=cats[cat_name].id,
                expiration_date=datetime.utcnow() + timedelta(days=days_expiry),
                manufacturer="Lab. Farmacéutico S.A.",
            )
            db.add(m)
            db.flush()
        created_meds.append(m)
    db.commit()
    print(f"✓ {len(created_meds)} medicamentos")

    # ── Movimientos históricos (12 meses de consumo) ─────────────────────
    total_movements = 0
    for med in created_meds:
        # Consumo diario base aleatorio entre 2 y 15
        base_daily = random.uniform(2, 15)
        for days_ago in range(365, 0, -1):
            if random.random() < 0.7:   # 70% de días hay movimiento
                date = datetime.utcnow() - timedelta(days=days_ago)
                # Estacionalidad: pico en invierno (meses 5-8 en Perú)
                month = date.month
                seasonal = 1.3 if month in (5, 6, 7, 8) else 1.0
                qty = max(1, round(base_daily * seasonal * random.uniform(0.7, 1.3)))

                mv = Movement(
                    medication_id=med.id,
                    date=date,
                    type=MovementType.OUT,
                    quantity=float(qty),
                    notes="Consumo registrado",
                )
                db.add(mv)
                total_movements += 1

        # Algunas entradas (reabastecimiento)
        for _ in range(6):
            days_ago = random.randint(1, 365)
            mv = Movement(
                medication_id=med.id,
                date=datetime.utcnow() - timedelta(days=days_ago),
                type=MovementType.IN,
                quantity=float(random.randint(100, 500)),
                notes="Reabastecimiento",
            )
            db.add(mv)
            total_movements += 1

    db.commit()
    print(f"✓ {total_movements} movimientos históricos")
    print("\n✅ Seed completado. Abre http://localhost:9002 para ver los datos.")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    raise
finally:
    db.close()
