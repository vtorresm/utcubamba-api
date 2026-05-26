from fastapi import APIRouter
from .endpoints import (
    auth,
    users,
    medications,
    predictions,
    categories,
    prediction_metrics,
    notifications,
    orders,
    reports
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(prediction_metrics.router, prefix="", tags=["prediction-metrics"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
