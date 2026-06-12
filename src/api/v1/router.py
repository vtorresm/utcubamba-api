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
    reports,
    forecasts,
    suppliers,
    lots,
    audits,
    deliveries,
    historical_uploads,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(medications.router, prefix="/medications", tags=["medications"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(historical_uploads.router, prefix="/predictions", tags=["historical-uploads"])
api_router.include_router(prediction_metrics.router, prefix="", tags=["prediction-metrics"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(forecasts.router, prefix="/forecasts", tags=["forecasts"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(lots.router, prefix="/lots", tags=["lots"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(deliveries.router, prefix="/deliveries", tags=["deliveries"])
