from fastapi import APIRouter
from src.api.v1.endpoints import predictions

router = APIRouter()
router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])