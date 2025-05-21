from fastapi import APIRouter
from .endpoints import auth, users, medications, predictions

# Crear el router principal de la API v1
api_router = APIRouter()

# Incluir los routers de cada módulo
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
