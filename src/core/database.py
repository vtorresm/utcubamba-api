import os
import sys
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

# Cargar variables de entorno
load_dotenv()

# Configura la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/utcubamba_db")
SQLALCHEMY_DATABASE_URL = DATABASE_URL  # Alias para compatibilidad con Alembic

# Crear el motor de SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # Habilita el logging de SQL (desactivar en producción)
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_recycle=300,  # Reciclar conexiones después de 5 minutos
)

def import_models():
    """Importa todos los modelos para que SQLModel los registre"""
    # Importar modelos manualmente para asegurar que se registren con SQLAlchemy
    try:
        # Importar todos los modelos para que se registren con SQLAlchemy
        from src.models import (
            User, UserCreate, UserUpdate, UserInDB,
            Category, CategoryCreate, CategoryUpdate, CategoryInDB,
            Condition, ConditionCreate, ConditionUpdate, ConditionInDB,
            IntakeType, IntakeTypeCreate, IntakeTypeUpdate, IntakeTypeInDB,
            Medication, MedicationCreate, MedicationUpdate, MedicationInDB,
            Movement, MovementCreate, MovementUpdate, MovementInDB,
            Prediction, PredictionCreate, PredictionUpdate, PredictionInDB,
            MedicationConditionLink
        )
        print("Modelos importados correctamente")
    except ImportError as e:
        print(f"Error al importar modelos: {e}")
        raise

def create_db_and_tables():
    """Crea todas las tablas definidas en los modelos SQLModel"""
    # Asegurarse de que los modelos estén importados
    import_models()
    
    # Crear todas las tablas
    print("Creando tablas de la base de datos...")
    SQLModel.metadata.create_all(engine)
    print("¡Tablas creadas exitosamente!")


def get_db() -> Generator[Session, None, None]:
    """Dependencia para obtener una sesión de base de datos"""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# Asegurarse de que los modelos estén importados cuando se importe este módulo
import_models()