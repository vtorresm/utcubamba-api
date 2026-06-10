"""
Seed de 6 usuarios con diferentes roles para MedInventory.
Ejecutar: docker compose exec api python scripts/seed_users.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import SessionLocal
from src.models.user import User
from src.models.base import Role, UserStatus

USERS = [
    {
        "nombre":       "Carlos Mendoza",
        "email":        "c.mendoza@hospital.pe",
        "password":     "Admin2024!",
        "cargo":        "Jefe de Sistemas",
        "departamento": "Sistemas",
        "contacto":     "999001001",
        "role":         Role.ADMIN,
    },
    {
        "nombre":       "María García",
        "email":        "m.garcia@hospital.pe",
        "password":     "Farmacia2024!",
        "cargo":        "Jefa de Farmacia",
        "departamento": "Farmacia",
        "contacto":     "999001002",
        "role":         Role.FARMACIA,
    },
    {
        "nombre":       "Luis Torres",
        "email":        "l.torres@hospital.pe",
        "password":     "Farmacia2024!",
        "cargo":        "Auxiliar de Farmacia",
        "departamento": "Farmacia",
        "contacto":     "999001003",
        "role":         Role.FARMACIA,
    },
    {
        "nombre":       "Ana Flores",
        "email":        "a.flores@hospital.pe",
        "password":     "Enfermeria2024!",
        "cargo":        "Jefa de Enfermería",
        "departamento": "Enfermería",
        "contacto":     "999001004",
        "role":         Role.ENFERMERIA,
    },
    {
        "nombre":       "Pedro Ríos",
        "email":        "p.rios@hospital.pe",
        "password":     "Enfermeria2024!",
        "cargo":        "Técnico en Enfermería",
        "departamento": "Enfermería",
        "contacto":     "999001005",
        "role":         Role.ENFERMERIA,
    },
    {
        "nombre":       "Elena Vargas",
        "email":        "e.vargas@hospital.pe",
        "password":     "Usuario2024!",
        "cargo":        "Personal Administrativo",
        "departamento": "Administración",
        "contacto":     "999001006",
        "role":         Role.USER,
    },
]

def seed():
    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        for data in USERS:
            existing = db.query(User).filter(User.email == data["email"]).first()
            if existing:
                print(f"  ⚠  Ya existe: {data['email']}")
                skipped += 1
                continue

            user = User(
                nombre=data["nombre"],
                email=data["email"],
                hashed_password=User.hash_password(data["password"]),
                cargo=data["cargo"],
                departamento=data["departamento"],
                contacto=data.get("contacto"),
                role=data["role"],
                estado=UserStatus.ACTIVO,
            )
            db.add(user)
            created += 1
            print(f"  ✓  Creado: {data['nombre']} ({data['role'].value}) — {data['email']}")

        db.commit()
        print(f"\n✅ Seed completado: {created} creados, {skipped} omitidos.")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding usuarios...\n")
    seed()
