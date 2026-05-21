from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from src.api.v1.router import api_router
from src.core.database import engine, create_db_and_tables
from src.core.limiter import limiter
from src.core.logging import setup_logging
from src.core.config import settings
import logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Configuración de CORS - Solo permitir el origen del frontend
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]

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
    La API utiliza autenticación JWT. Incluya el token en el encabezado `Authorization: Bearer <token>`
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

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
    logger.error("Error de validación en %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
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

