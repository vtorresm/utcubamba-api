import os
import sys
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

# Cargar variables de entorno
print("🔍 Cargando variables de entorno...")
load_dotenv()

# Configura la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/utcubamba_db")
SQLALCHEMY_DATABASE_URL = DATABASE_URL  # Alias para compatibilidad con Alembic
print(f"🔗 URL de la base de datos: {SQLALCHEMY_DATABASE_URL}")

# Crear el motor de SQLAlchemy
print("🔧 Creando motor de base de datos...")
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True,  # Habilita el logging de SQL (desactivar en producción)
        pool_pre_ping=True,  # Verifica la conexión antes de usarla
        pool_recycle=300,  # Reciclar conexiones después de 5 minutos
    )
    print("✅ Motor de base de datos creado exitosamente")
except Exception as e:
    print(f"❌ Error al crear el motor de la base de datos: {e}")
    raise

def import_models():
    """Importa todos los modelos para que SQLModel los registre"""
    print("🔍 Iniciando importación de modelos...")
    # Importar modelos manualmente para asegurar que se registren con SQLAlchemy
    try:
        print("🔍 Intentando importar modelos individuales...")
        # Importar todos los modelos para que se registren con SQLAlchemy
        from src.models.user import User, UserCreate, UserUpdate, UserInDB
        print("✅ Modelos de usuario importados")
        from src.models.category import Category, CategoryCreate, CategoryUpdate, CategoryInDB
        print("✅ Modelos de categoría importados")
        from src.models.condition import Condition, ConditionCreate, ConditionUpdate, ConditionInDB
        print("✅ Modelos de condición importados")
        from src.models.intake_type import IntakeType, IntakeTypeCreate, IntakeTypeUpdate, IntakeTypeInDB
        print("✅ Modelos de tipo de ingesta importados")
        from src.models.medication import Medication, MedicationCreate, MedicationUpdate, MedicationInDB
        print("✅ Modelos de medicamento importados")
        from src.models.movement import Movement, MovementCreate, MovementUpdate, MovementInDB
        print("✅ Modelos de movimiento importados")
        from src.models.prediction import Prediction, PredictionCreate, PredictionUpdate, PredictionInDB
        print("✅ Modelos de predicción importados")
        from src.models.medication_condition import MedicationConditionLink
        print("✅ Modelo de enlace medicamento-condición importado")
        
        print("✅ Todos los modelos importados correctamente")
    except ImportError as e:
        print(f"❌ Error al importar modelos: {e}")
        import traceback
        traceback.print_exc()
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