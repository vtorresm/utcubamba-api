from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth, users, medicamentos
from src.db.init_db import init_db
from src.core.logging import setup_logging

# Configurar logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application and initializing database")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down application")

app = FastAPI(
    title="User CRUD API with Authentication, Roles, and Medicamentos",
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(medicamentos.router, prefix="/medicamentos", tags=["medicamentos"])
app.include_router(reportes.router, prefix="/reportes", tags=["reportes"])  # Nuevo router

if __name__ == "__main__":
    import uvicorn
    logger.info("Running Uvicorn server")
    uvicorn.run(app, host="0.0.0.0", port=8000)