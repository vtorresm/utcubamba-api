from alembic.config import Config
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Crear configuración de Alembic
alembic_cfg = Config()
alembic_cfg.set_main_option('script_location', 'src/migrations')
alembic_cfg.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))

# Guardar configuración temporal
with open('alembic.ini', 'w') as f:
    alembic_cfg.write(f)

print("Configuración de Alembic guardada exitosamente!")
