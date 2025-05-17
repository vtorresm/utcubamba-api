from fastapi import FastAPI
from src.api.v1.router import api_router
from src.core.database import engine
from src.models import Base
from src.core.logging import setup_logging

# Configurar logging
setup_logging()

app = FastAPI(title="Utcubamba API", version="1.0.0")

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Registrar rutas
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Utcubamba API is running"}