from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from src.api.v1.router import api_router
from src.core.database import engine, create_db_and_tables
from src.core.limiter import limiter
from src.core.logging import setup_logging
from src.core.config import settings
from src.exceptions import (
    DomainError, NotFoundError, ForbiddenError, ValidationError
)
import logging

setup_logging()
logger = logging.getLogger(__name__)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


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
        "email": settings.CONTACT_EMAIL,
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
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
        },
        {
            "name": "notifications",
            "description": "Notificaciones y alertas del sistema"
        },
        {
            "name": "orders",
            "description": "Órdenes de pedido y reabastecimiento"
        },
        {
            "name": "reports",
            "description": "Reportes generados del sistema"
        }
    ]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Disposition"],
    max_age=600
)


@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    if isinstance(exc, NotFoundError):
        status_code = 404
    elif isinstance(exc, ForbiddenError):
        status_code = 403
    elif isinstance(exc, ValidationError):
        status_code = 400
    else:
        status_code = 500
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("Error de validación en %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Utcubamba API is running"}
