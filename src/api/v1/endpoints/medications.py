from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.database import get_db
from src.models.medication import Medication, MedicationCreate
from src.models.category import Category
from src.models.intake_type import IntakeType
from src.schemas.medication import MedicationResponse, MedicationCreate, MedicationUpdate

# Comentado temporalmente hasta que la autenticación esté lista
from src.dependencies.auth import get_current_user
from src.models.user import User, Role

# Deshabilitar temporalmente la autenticación
AUTH_ENABLED = False

router = APIRouter()

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
    db: Session = Depends(get_db),
    # Descomenta la siguiente línea cuando la autenticación esté lista
    # current_user: User = Depends(get_current_user) if AUTH_ENABLED else None
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
        
        # Construir la consulta base con joinedload para cargar las relaciones
        query = db.query(Medication).options(
            joinedload(Medication.category),
            joinedload(Medication.intake_type)
        )
        
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
        meds_list = []
        for med in medications:
            try:
                # Crear un diccionario con los atributos del modelo
                med_dict = {
                    'id': med.id,
                    'name': med.name,
                    'description': med.description,
                    'stock': med.stock,
                    'min_stock': med.min_stock,
                    'unit': med.unit,
                    'manufacturer': med.manufacturer,
                    'expiration_date': med.expiration_date.isoformat() if med.expiration_date else None,
                    'status': med.status,
                    'price': float(med.price) if med.price is not None else 0.0,
                    'category_id': med.category_id,
                    'intake_type_id': med.intake_type_id,
                    'created_at': med.created_at.isoformat() if hasattr(med, 'created_at') and med.created_at else None,
                    'updated_at': med.updated_at.isoformat() if hasattr(med, 'updated_at') and med.updated_at else None,
                    'barcode': getattr(med, 'barcode', None),
                    'location': getattr(med, 'location', None),
                    'notes': getattr(med, 'notes', None)
                }
                
                # Añadir la categoría si existe
                if med.category:
                    med_dict['category'] = {
                        'id': med.category.id,
                        'name': med.category.name,
                        'description': med.category.description
                    }
                
                # Añadir el tipo de ingesta si existe
                if med.intake_type:
                    med_dict['intake_type'] = {
                        'id': med.intake_type.id,
                        'name': med.intake_type.name,
                        'description': med.intake_type.description if hasattr(med.intake_type, 'description') else None
                    }
                else:
                    med_dict['intake_type'] = None
                
                # Asegurarse de que todos los campos requeridos estén presentes
                if 'category' not in med_dict:
                    med_dict['category'] = None
                if 'intake_type' not in med_dict:
                    med_dict['intake_type'] = None
                
                # Convertir a la respuesta usando el modelo
                response_med = MedicationResponse.from_orm(med)
                med_dict.update(response_med.dict())
                meds_list.append(med_dict)
            except Exception as e:
                print(f"Error procesando medicamento {med.id if hasattr(med, 'id') else 'unknown'}: {str(e)}")
                # Añadir un registro de error a la lista para que la respuesta sea consistente
                meds_list.append({
                    'id': med.id if hasattr(med, 'id') else 0,
                    'name': f'Error: {str(e)[:100]}',
                    'error': True
                })
                continue
        
        return {
            "status": "success",
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(meds_list),
            "items": meds_list
        }
        
    except Exception as e:
        print(f"Error en endpoint de medicamentos: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener los medicamentos: {str(e)}"
        )

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
    db: Session = Depends(get_db),
    # Descomenta la siguiente línea cuando la autenticación esté lista
    # current_user: User = Depends(get_current_user) if AUTH_ENABLED else None
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new medication.
    """
    # Check if authentication is enabled and user has admin permissions
    if AUTH_ENABLED and (not current_user or current_user.role != Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        # Verificar si la categoría existe si se proporciona
        if medication.category_id is not None:
            category = db.get(Category, medication.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id {medication.category_id} not found"
                )
        
        # Verificar si el tipo de ingesta existe si se proporciona
        if medication.intake_type_id is not None:
            intake_type = db.get(IntakeType, medication.intake_type_id)
            if not intake_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Intake type with id {medication.intake_type_id} not found"
                )
        
        # Crear el medicamento
        medication_data = medication.model_dump(exclude={"condition_ids"})
        db_medication = Medication(**medication_data)
        
        # Agregar condiciones si se proporcionan
        if hasattr(medication, 'condition_ids') and medication.condition_ids:
            from src.models.condition import Condition
            from src.models.medication_condition import MedicationConditionLink
            
            for condition_id in medication.condition_ids:
                condition = db.get(Condition, condition_id)
                if not condition:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Condition with id {condition_id} not found"
                    )
                # Crear la relación many-to-many
                db_medication.condition_links.append(
                    MedicationConditionLink(condition=condition)
                )
        
        db.add(db_medication)
        db.commit()
        db.refresh(db_medication)
        
        return db_medication
        
    except Exception as e:
        db.rollback()
        print(f"Error al crear el medicamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el medicamento: {str(e)}"
        )

# Update medication
@router.put("/{medication_id}", response_model=Dict[str, Any])
def update_medication(
    medication_id: int,
    medication: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza un medicamento existente (sin autenticación temporalmente).
    """
    try:
        print(f"\n=== SOLICITUD PUT /medications/{medication_id} ===")
        print(f"Datos recibidos: {medication}")
        
        # Obtener el medicamento
        db_medication = db.query(Medication).filter(Medication.id == medication_id).first()
        if not db_medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el medicamento con ID {medication_id}"
            )
        
        # Actualizar solo los campos proporcionados
        update_data = {k: v for k, v in medication.items() if v is not None}
        print(f"Actualizando con datos: {update_data}")
        
        for key, value in update_data.items():
            if hasattr(db_medication, key):
                setattr(db_medication, key, value)
        
        db.add(db_medication)
        db.commit()
        db.refresh(db_medication)
        
        print(f"Medicamento actualizado exitosamente: {db_medication}")
        
        return {
            "status": "success",
            "message": "Medicamento actualizado exitosamente",
            "data": MedicationResponse.from_orm(db_medication).dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar el medicamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el medicamento: {str(e)}"
        )

# Delete medication
@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) if AUTH_ENABLED else None
):
    """
    Delete a medication.
    
    Args:
        medication_id: ID of the medication to delete
        
    Returns:
        None (204 No Content on success)
        
    Raises:
        HTTPException: 403 if user is not admin (when auth is enabled)
        HTTPException: 404 if medication not found
        HTTPException: 500 if there's a server error
    """
    try:
        # Check if user has admin permissions (only when auth is enabled)
        if AUTH_ENABLED and (current_user is None or current_user.role != Role.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get the medication
        db_medication = db.query(Medication).filter(Medication.id == medication_id).first()
        if db_medication is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Delete the medication
        db.delete(db_medication)
        db.commit()
        
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 403, 404) as is
        raise
        
    except Exception as e:
        # Log the error and return 500 for any other exceptions
        print(f"Error deleting medication {medication_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting medication: {str(e)}"
        )
