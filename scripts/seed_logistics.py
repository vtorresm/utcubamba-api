"""
Script para sembrar datos de ejemplo de Logística:
Proveedores, Lotes/Trazabilidad, Auditorías y Entregas.

Ejecutar desde el contenedor:
  docker compose exec api python scripts/seed_logistics.py
"""
from datetime import datetime, timedelta, date
import random

from src.core.database import SessionLocal
from src.models.user import User, Role
from src.models.medication import Medication
from src.models.supplier import Supplier, SupplierStatus
from src.models.lot import Lot, LotStatus, LotEvent
from src.models.audit import Audit, AuditStatus
from src.models.delivery import Delivery, DeliveryStatus

db = SessionLocal()

try:
    # ── Responsable para auditorías ──────────────────────────────────────────
    responsible = (
        db.query(User).filter(User.role.in_([Role.ADMIN, Role.FARMACIA])).first()
    )
    if not responsible:
        responsible = db.query(User).first()
    if not responsible:
        raise RuntimeError("No hay usuarios en la base de datos. Crea un usuario primero.")

    medications = db.query(Medication).all()
    if not medications:
        raise RuntimeError("No hay medicamentos en la base de datos. Ejecuta seed_medications.py primero.")

    # ── Proveedores ──────────────────────────────────────────────────────────
    suppliers_data = [
        ("FarmaCorp S.A.",      "Distribuidor mayorista", "Carla Reyes",    "carla.reyes@farmacorp.com",   "+51 941 200 311", 92, 95, SupplierStatus.ACTIVE),
        ("MediSupply Perú",     "Laboratorio",            "Jorge Tello",    "jtello@medisupply.pe",        "+51 987 433 122", 85, 88, SupplierStatus.ACTIVE),
        ("Andina Farmacéutica", "Distribuidor regional",  "Luz Pacheco",    "lpacheco@andinafarma.com",    "+51 956 712 044", 78, 81, SupplierStatus.ACTIVE),
        ("BioGen Labs",         "Laboratorio",            "Renzo Castillo", "rcastillo@biogenlabs.com",    "+51 933 280 765", 88, 90, SupplierStatus.ACTIVE),
        ("NorPharma E.I.R.L.",  "Distribuidor regional",  "Diana Soto",     "dsoto@norpharma.pe",          "+51 945 110 982", 65, 70, SupplierStatus.INACTIVE),
    ]
    suppliers = []
    for name, category, contact_name, contact_email, contact_phone, reliability, quality, status in suppliers_data:
        s = db.query(Supplier).filter(Supplier.name == name).first()
        if not s:
            s = Supplier(
                name=name,
                category=category,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                reliability_score=reliability,
                quality_score=quality,
                description=f"Proveedor de {category.lower()} con historial de entregas registrado en el sistema.",
                status=status,
            )
            db.add(s)
            db.flush()
        suppliers.append(s)
    db.commit()
    print(f"✓ {len(suppliers)} proveedores")

    # ── Lotes + eventos de trazabilidad ──────────────────────────────────────
    lot_status_cycle = [LotStatus.STORED, LotStatus.QUALITY_CHECK, LotStatus.DISPATCHED, LotStatus.RECEIVED]
    locations = ["Almacén Central - Pasillo A", "Almacén Central - Pasillo B", "Cámara Fría 1", "Cámara Fría 2", "Almacén Norte"]

    created_lots = 0
    for i, med in enumerate(medications[:8]):
        code = f"LOT-{2026}{(i + 1):03d}"
        existing = db.query(Lot).filter(Lot.code == code).first()
        if existing:
            continue

        status = lot_status_cycle[i % len(lot_status_cycle)]
        manufactured = date.today() - timedelta(days=random.randint(60, 300))
        expiration = manufactured + timedelta(days=random.randint(365, 730))

        lot = Lot(
            code=code,
            medication_id=med.id,
            quantity=random.randint(50, 500),
            location=random.choice(locations),
            temperature=round(random.uniform(15.0, 25.0), 1),
            humidity=round(random.uniform(35.0, 60.0), 1),
            manufactured_date=manufactured,
            expiration_date=expiration,
            status=status,
            notes=f"Lote de {med.name} ingresado para control de trazabilidad.",
        )
        db.add(lot)
        db.flush()

        steps = [
            ("Recibido en almacén", "Verificación de documentación y conteo físico", True),
            ("Inspección de calidad", "Revisión de condiciones de transporte y empaque", status != LotStatus.RECEIVED),
            ("Almacenado", "Ubicado en zona asignada según condiciones de conservación", status in [LotStatus.STORED, LotStatus.DISPATCHED]),
            ("Despachado", "Lote despachado a punto de distribución", status == LotStatus.DISPATCHED),
        ]
        base_date = datetime.combine(manufactured, datetime.min.time()) + timedelta(days=5)
        for order, (title, detail, completed) in enumerate(steps):
            db.add(LotEvent(
                lot_id=lot.id,
                title=title,
                detail=detail,
                event_date=base_date + timedelta(days=order * 3),
                completed=completed,
                step_order=order,
            ))
        created_lots += 1

    db.commit()
    print(f"✓ {created_lots} lotes con trazabilidad")

    # ── Auditorías ───────────────────────────────────────────────────────────
    audits_data = [
        ("Almacén Central",        96.0, 0.97, AuditStatus.COMPLETED,   "Sin observaciones relevantes."),
        ("Cámara Fría 1",          88.0, 0.91, AuditStatus.COMPLETED,   "Se recomienda calibrar sensores de temperatura."),
        ("Farmacia - Dispensario", 74.0, 0.83, AuditStatus.IN_PROGRESS, "Pendiente revisión de lotes próximos a vencer."),
        ("Almacén Norte",          60.0, 0.72, AuditStatus.REJECTED,    "Documentación incompleta; requiere nueva visita."),
    ]
    created_audits = 0
    for i, (sector, doc_score, prec_score, status, notes) in enumerate(audits_data):
        existing = db.query(Audit).filter(Audit.sector == sector, Audit.notes == notes).first()
        if existing:
            continue
        db.add(Audit(
            sector=sector,
            audit_date=datetime.utcnow() - timedelta(days=(i + 1) * 9),
            documentation_score=doc_score,
            precision_score=prec_score,
            status=status,
            notes=notes,
            responsible_id=responsible.id,
        ))
        created_audits += 1
    db.commit()
    print(f"✓ {created_audits} auditorías")

    # ── Entregas ─────────────────────────────────────────────────────────────
    deliveries_data = [
        (0, "Ibuprofeno 400mg",        300, DeliveryStatus.RECEIVED,           -2, True),
        (1, "Amoxicilina 500mg",       250, DeliveryStatus.RECEIVED,           -5, True),
        (0, "Paracetamol 500mg",       500, DeliveryStatus.PENDING_INSPECTION,  0, False),
        (2, "Loratadina 10mg",         150, DeliveryStatus.IN_TRANSIT,          3, False),
        (3, "Insulina Glargina 100UI",  60, DeliveryStatus.IN_TRANSIT,          5, False),
        (1, "Salbutamol Inhalador",    120, DeliveryStatus.PENDING_INSPECTION,  1, False),
    ]
    med_by_name = {m.name: m for m in medications}
    created_deliveries = 0
    for supplier_idx, product, quantity, status, eta_offset_days, received in deliveries_data:
        existing = db.query(Delivery).filter(Delivery.product == product, Delivery.quantity == quantity).first()
        if existing:
            continue
        med = med_by_name.get(product)
        eta = datetime.utcnow() + timedelta(days=eta_offset_days)
        db.add(Delivery(
            supplier_id=suppliers[supplier_idx].id,
            medication_id=med.id if med else None,
            product=product,
            quantity=quantity,
            status=status,
            eta=eta,
            received_at=eta if received else None,
            notes="Entrega registrada automáticamente por el sistema de seed.",
        ))
        created_deliveries += 1
    db.commit()
    print(f"✓ {created_deliveries} entregas")

    print("\n✅ Datos de logística sembrados correctamente.")

except Exception as exc:
    db.rollback()
    print(f"✗ Error sembrando datos de logística: {exc}")
    raise
finally:
    db.close()
