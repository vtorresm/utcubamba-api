from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .medicamentos import router as medicamentos_router
from .movimientos import router as movimientos_router
from .reportes import router as reportes_router
from .alertas import router as alertas_router  # Nuevo

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(medicamentos_router, prefix="/medicamentos", tags=["medicamentos"])
router.include_router(movimientos_router, prefix="/movimientos", tags=["movimientos"])
router.include_router(reportes_router, prefix="/reportes", tags=["reportes"])
router.include_router(alertas_router, prefix="/alertas", tags=["alertas"])  # Nuevo
router.include_router(predicciones_router, prefix="/predicciones", tags=["predicciones"])  # Nuevo