from fastapi import APIRouter
from .endpoints import auth, users, medications, predictions, categories

# Crear el router principal de la API v1
api_router = APIRouter()

# Incluir los routers de cada módulo
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
