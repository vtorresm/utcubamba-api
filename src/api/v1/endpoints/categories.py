from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from src.core.database import get_db
from src.models.category import Category
from src.schemas.category import CategoryResponse
from src.dependencies.auth import get_current_user
from src.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=List[CategoryResponse],
    summary="Listar categorías",
    description="Obtiene una lista de todas las categorías disponibles.",
    response_description="Lista de categorías",
)
def get_categories(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return db.query(Category).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error("Error al obtener categorías: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Error interno del servidor"},
        )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Obtener categoría por ID",
    description="Obtiene una categoría específica por su ID.",
    response_description="Categoría solicitada",
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {category_id} no encontrada",
        )
    return category
