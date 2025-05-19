from fastapi import APIRouter
from src.api.v1.endpoints import predictions, auth

router = APIRouter()
router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])