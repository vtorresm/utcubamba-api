from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.core.database import get_db
from src.models.category import Category, CategoryCreate, CategoryUpdate, CategoryInDB
from src.schemas.category import CategoryResponse

# Comentado temporalmente hasta que la autenticación esté lista
# from src.dependencies.auth import get_current_user
# from src.models.user import User, Role

# Deshabilitar temporalmente la autenticación
AUTH_ENABLED = False

router = APIRouter()

# Get all categories
@router.get(
    "/", 
    response_model=List[CategoryResponse],
    summary="Listar categorías",
    description="Obtiene una lista de todas las categorías disponibles.",
    response_description="Lista de categorías"
)
def get_categories(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db),
    # Descomenta la siguiente línea cuando la autenticación esté lista
    # current_user: User = Depends(get_current_user) if AUTH_ENABLED else None
):
    """
    Obtiene una lista de todas las categorías disponibles.
    
    Parámetros:
    - skip: Número de registros a omitir (para paginación)
    - limit: Número máximo de registros a devolver (máx. 1000)
    
    Retorna una lista de categorías.
    """
    try:
        categories = db.query(Category).offset(skip).limit(limit).all()
        return categories
    except Exception as e:
        print(f"Error al obtener categorías: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener las categorías"
        )

# Get category by ID
@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Obtener categoría por ID",
    description="Obtiene una categoría específica por su ID.",
    response_description="Categoría solicitada"
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    # Descomenta la siguiente línea cuando la autenticación esté lista
    # current_user: User = Depends(get_current_user) if AUTH_ENABLED else None
):
    """
    Obtiene una categoría específica por su ID.
    
    Parámetros:
    - category_id: ID de la categoría a buscar
    
    Retorna la categoría si se encuentra, de lo contrario devuelve un error 404.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {category_id} no encontrada"
        )
    return category
