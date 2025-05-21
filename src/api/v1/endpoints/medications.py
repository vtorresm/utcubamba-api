from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import text, select, and_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime

from src.core.database import get_db
from src.models.medication import Medication, MedicationBase, MedicationCreate, MedicationUpdate, MedicationInDB
from src.models.category import Category, CategoryBase
from src.models.intake_type import IntakeType, IntakeTypeBase
from src.dependencies.auth import get_current_user
from src.models.user import User

router = APIRouter()

# Pydantic models for response
class MedicationResponse(MedicationInDB):
    """
    Modelo de respuesta para medicamentos.
    
    Atributos:
    - id: Identificador único del medicamento
    - name: Nombre del medicamento
    - description: Descripción detallada (opcional)
    - stock: Cantidad actual en inventario
    - min_stock: Nivel mínimo de inventario antes de alertar
    - unit: Unidad de medida (ej. mg, ml, unidades)
    - category_id: ID de la categoría a la que pertenece
    - intake_type_id: ID del tipo de ingesta
    - created_at: Fecha de creación
    - updated_at: Fecha de última actualización
    """
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Paracetamol 500mg",
                "description": "Analgésico y antipirético",
                "stock": 150,
                "min_stock": 10,
                "unit": "units",
                "category_id": 1,
                "intake_type_id": 1,
                "created_at": "2025-01-15T10:00:00",
                "updated_at": "2025-05-20T15:30:00"
            }
        }

# Test endpoint
@router.get(
    "/test",
    summary="Endpoint de prueba",
    description="Verifica que el módulo de medicamentos esté funcionando correctamente.",
    response_description="Mensaje de confirmación"
)
def test_endpoint():
    """
    Endpoint de prueba para verificar el funcionamiento del módulo de medicamentos.
    
    Returns:
        dict: Mensaje de confirmación del estado del endpoint
    """
    return {"message": "El endpoint de medicamentos está funcionando correctamente"}

# Get all medications
@router.get(
    "/", 
    response_model=Dict[str, Any],
    summary="Listar medicamentos",
    description="Obtiene una lista paginada de medicamentos con filtros opcionales.",
    response_description="Diccionario con la lista de medicamentos y metadatos de paginación"
)
def get_medications(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(10, ge=1, le=100, description="Número de registros a devolver"),
    name: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    category_id: Optional[int] = Query(None, description="Filtrar por ID de categoría"),
    intake_type_id: Optional[int] = Query(None, description="Filtrar por ID de tipo de ingesta"),
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Descomentar cuando la autenticación esté lista
):
    """
    Obtiene una lista paginada de medicamentos con filtros opcionales.
    
    Parámetros:
    - skip: Número de registros a omitir (para paginación)
    - limit: Número máximo de registros a devolver (máx. 100)
    - name: Filtrar por nombre (búsqueda parcial)
    - category_id: Filtrar por ID de categoría
    - intake_type_id: Filtrar por ID de tipo de ingesta
    
    Retorna un diccionario con los resultados y metadatos de paginación.
    """
    try:
        print(f"\n=== SOLICITUD GET /medications/ ===")
        print(f"Parámetros: skip={skip}, limit={limit}, name={name}, category_id={category_id}")
        
        # Construir la consulta base
        query = db.query(Medication)
        
        # Aplicar filtros si se proporcionan
        if name:
            query = query.filter(Medication.name.ilike(f'%{name}%'))
            print(f"Aplicando filtro por nombre: {name}")
            
        if category_id is not None:
            query = query.filter(Medication.category_id == category_id)
            print(f"Aplicando filtro por categoría: {category_id}")
            
        if intake_type_id is not None:
            query = query.filter(Medication.intake_type_id == intake_type_id)
            print(f"Aplicando filtro por tipo de ingesta: {intake_type_id}")
        
        # Obtener el total de registros (para paginación)
        total = query.count()
        
        # Aplicar paginación
        medications = query.offset(skip).limit(limit).all()
        
        # Convertir los resultados a diccionario usando el modelo de respuesta
        meds_list = [
            MedicationResponse.from_orm(med).dict()
            for med in medications
        ]
        
        return {
            "status": "success",
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(meds_list),
            "data": meds_list
        }
        
    except Exception as e:
        print(f"Error en endpoint simplificado: {str(e)}")
        return [{"error": str(e)}]

# Get specific medication by ID
@router.get(
    "/{medication_id}", 
    response_model=Dict[str, Any],
    summary="Obtener medicamento por ID",
    description="Obtiene los detalles de un medicamento específico por su ID.",
    response_description="Diccionario con los datos del medicamento solicitado",
    responses={
        200: {"description": "Medicamento encontrado exitosamente"},
        404: {"description": "No se encontró el medicamento con el ID especificado"},
        500: {"description": "Error interno del servidor"}
    }
)
def get_medication(
    medication_id: int = Path(..., description="ID del medicamento"),
    db: Session = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Descomentar cuando la autenticación esté lista
):
    """
    Obtiene un medicamento específico por su ID.
    
    Parámetros:
    - medication_id: ID del medicamento a buscar
    
    Retorna el medicamento si se encuentra, de lo contrario devuelve un error 404.
    """
    try:
        print(f"\n=== SOLICITUD GET /medications/{medication_id} ===")
        
        # Buscar el medicamento por ID
        medication = db.query(Medication).filter(Medication.id == medication_id).first()
        
        if medication is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el medicamento con ID {medication_id}"
            )
        
        # Convertir a diccionario usando el modelo de respuesta
        return {
            "status": "success",
            "data": MedicationResponse.from_orm(medication).dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al obtener el medicamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el medicamento: {str(e)}"
        )

# Create new medication
@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
def create_medication(
    medication: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new medication.
    """
    # Check if user has admin permissions
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # TODO: Replace with actual Medication model import
    # For now, using a mock implementation for testing
    from src.models import Medication
    
    # Create new medication
    db_medication = Medication(**medication.model_dump())
    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)
    return db_medication

# Update medication
@router.put("/{medication_id}", response_model=MedicationResponse)
def update_medication(
    medication_id: int,
    medication: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing medication.
    """
    # Check if user has admin permissions
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # TODO: Replace with actual Medication model import
    from src.models import Medication
    
    # Get the medication
    db_medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if db_medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    # Update medication fields
    medication_data = medication.model_dump(exclude_unset=True)
    for key, value in medication_data.items():
        setattr(db_medication, key, value)
    
    db.commit()
    db.refresh(db_medication)
    return db_medication

# Delete medication
@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a medication.
    """
    # Check if user has admin permissions
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # TODO: Replace with actual Medication model import
    from src.models import Medication
    
    # Get the medication
    db_medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if db_medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    # Delete the medication
    db.delete(db_medication)
    db.commit()
    return None

