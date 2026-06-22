#!/usr/bin/env python3
"""
Script para crear un usuario de prueba en la base de datos.
Uso: python seed_user.py
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.user import User, UserStatus, Role
from core.config import settings

def create_test_user():
    """Crea un usuario de prueba en la base de datos."""

    # Crear conexión a la BD
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Datos del usuario de prueba
        email = "test@hospital.pe"
        nombre = "Usuario Test"
        cargo = "Farmacéutico"
        departamento = "Farmacia"
        contacto = "+51987654321"
        password = "Test123456"

        # Verificar si el usuario ya existe
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"✓ El usuario {email} ya existe en la base de datos")
            return

        # Crear el usuario
        hashed_password = User.hash_password(password)
        new_user = User(
            nombre=nombre,
            email=email,
            hashed_password=hashed_password,
            cargo=cargo,
            departamento=departamento,
            contacto=contacto,
            role=Role.USER,
            estado=UserStatus.ACTIVO
        )

        # Guardar en la BD
        session.add(new_user)
        session.commit()

        print(f"✓ Usuario creado exitosamente")
        print(f"  Email: {email}")
        print(f"  Contraseña: {password}")
        print(f"  Rol: {Role.USER.value}")

    except Exception as e:
        session.rollback()
        print(f"✗ Error al crear el usuario: {str(e)}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    create_test_user()
