from alembic.config import Config
from alembic import command

def init_db():
    # Ejecutar migraciones de Alembic para inicializar la base de datos
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")