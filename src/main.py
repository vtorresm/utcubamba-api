from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.router import api_router
from src.core.database import engine, create_db_and_tables
from src.core.logging import setup_logging

# Configurar logging
setup_logging()

# Configuración de CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Crear la aplicación FastAPI
app = FastAPI(
    title="Utcubamba API",
    version="1.0.0",
    description="API para el sistema de predicción de desabastecimiento de medicamentos"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Evento de inicio para crear tablas
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Registrar rutas
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Utcubamba API is running"}

# Manejo de errores global
@app.exception_handler(Exception)
async def validation_exception_handler(request, exc):
    return {
        "status_code": 500,
        "message": "Internal Server Error",
        "details": str(exc)
    }