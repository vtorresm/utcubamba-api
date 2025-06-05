from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from src.api.v1.router import api_router
from src.core.database import engine, create_db_and_tables
from src.core.logging import setup_logging
import logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Configuración de CORS - Solo permitir el origen del frontend
origins = [
    "http://localhost:3000"
]

# Lista de métodos HTTP permitidos
allow_methods = ["*"]

# Lista de encabezados permitidos
# Crear la aplicación FastAPI
app = FastAPI(
    title="Utcubamba API",
    version="1.0.0",
    description="API para el sistema de predicción de desabastecimiento de medicamentos",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Disposition"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Manejador de excepciones global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Manejador para errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Error de validación: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
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