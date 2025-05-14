from sqlalchemy import create_engine
from src.models.database_models import Base
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Crear engine
engine = create_engine(os.getenv("DATABASE_URL"))

# Crear todas las tablas
Base.metadata.create_all(engine)

print("Tablas creadas exitosamente!")
