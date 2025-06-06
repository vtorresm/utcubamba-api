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
# Crear la aplicación FastAPI con metadatos mejorados
app = FastAPI(
    title="Utcubamba API",
    version="1.0.0",
    description="""
    ## API para el sistema de predicción de desabastecimiento de medicamentos
    
    Esta API proporciona endpoints para:
    - Predecir desabastecimientos de medicamentos
    - Gestionar predicciones históricas
    - Monitorear el rendimiento de los modelos de predicción
    - Gestionar métricas de modelos
    
    ### Autenticación
    La API utiliza autenticación JWT. Inclya el token en el encabezado `Authorization: Bearer <token>`
    """,
    contact={
        "name": "Soporte Técnico",
        "email": "soporte@utcubamba.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Autenticación y gestión de usuarios"
        },
        {
            "name": "users",
            "description": "Operaciones con usuarios"
        },
        {
            "name": "medications",
            "description": "Gestión de medicamentos"
        },
        {
            "name": "predictions",
            "description": "Predicciones de desabastecimiento"
        },
        {
            "name": "prediction-metrics",
            "description": "Métricas de rendimiento de modelos de predicción"
        },
        {
            "name": "categories",
            "description": "Categorías de medicamentos"
        }
    ]
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