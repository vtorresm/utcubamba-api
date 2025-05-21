from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from src.core.database import get_db
from src.models.user import User, Role
from src.dependencies.auth import get_current_user

router = APIRouter()

# Pydantic models for request/response
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    contacto: Optional[str] = None
    role: Optional[str] = None
    
    class Config:
        from_attributes = True
        
    def model_dump(self, **kwargs):
        # Filtrar valores None para actualizaciones parciales
        return {k: v for k, v in super().model_dump(**kwargs).items() if v is not None}

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True

# Get all users endpoint (admin only)
@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Retrieve all users.
    Only accessible to admin users.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# Get current user endpoint
@router.get("/me", response_model=UserResponse)
def get_user_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    """
    return current_user

# Get specific user by ID (admin only)
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.
    Only accessible to admin users.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Update user endpoint
@router.put("/me", response_model=UserResponse)
def update_user(
    user_data: UserBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information.
    
    - Solo los administradores pueden cambiar el rol de un usuario.
    - Los usuarios normales solo pueden actualizar sus propios datos, excepto el rol.
    """
    # Obtener datos actualizables
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Si el usuario no es administrador, asegurarse de que solo actualice sus propios datos
    if current_user.role != Role.ADMIN:
        # Eliminar campos que solo pueden ser modificados por administradores
        if "role" in update_data:
            del update_data["role"]
        if "email" in update_data:
            del update_data["email"]
        
        # Lista de campos permitidos para usuarios no administradores
        allowed_fields = ["nombre", "cargo", "departamento", "contacto"]
        
        # Filtrar solo los campos permitidos
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    # Validar unicidad del teléfono si se está actualizando
    if "contacto" in update_data and update_data["contacto"] is not None:
        existing_contact = db.query(User).filter(
            User.contacto == update_data["contacto"],
            User.id != current_user.id,
            User.contacto.isnot(None)
        ).first()
        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "contact_exists",
                    "message": "El número de teléfono ya está registrado con otro usuario"
                }
            )
    else:
        # Para administradores, validar el rol si se está actualizando
        if "role" in update_data:
            try:
                role_enum = Role(update_data["role"].lower())
                update_data["role"] = role_enum
            except ValueError:
                valid_roles = [r.value for r in Role]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "invalid_role",
                        "message": f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}"
                    }
                )
    
    # Si no hay campos para actualizar después del filtro
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "no_valid_fields",
                "message": "No se proporcionaron campos válidos para actualizar"
            }
        )
    
    # Actualizar solo los campos proporcionados
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    # Actualizar la fecha de modificación
    current_user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "update_failed",
                "message": f"Error al actualizar el usuario: {str(e)}"
            }
        )

# Admin update any user by ID
@router.put("/admin/{user_id}", response_model=UserResponse)
def admin_update_user(
    user_id: int,
    user_data: UserBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update any user information (admin only).
    
    - Solo los administradores pueden usar este endpoint.
    - Permite actualizar cualquier campo, incluyendo el rol.
    """
    # Verificar que el usuario actual sea administrador
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": "No tienes permisos para realizar esta acción"
            }
        )
    
    # Buscar el usuario a actualizar
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": f"Usuario con ID {user_id} no encontrado"
            }
        )
    
    # Obtener datos actualizables
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Validar unicidad del teléfono si se está actualizando
    if "contacto" in update_data and update_data["contacto"] is not None:
        existing_contact = db.query(User).filter(
            User.contacto == update_data["contacto"],
            User.id != user_id,
            User.contacto.isnot(None)
        ).first()
        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "contact_exists",
                    "message": "El número de teléfono ya está registrado con otro usuario"
                }
            )
    
    # Validar el rol si se está actualizando
    if "role" in update_data:
        try:
            role_enum = Role(update_data["role"].lower())
            update_data["role"] = role_enum
        except ValueError:
            valid_roles = [r.value for r in Role]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_role",
                    "message": f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}"
                }
            )
    
    # Actualizar solo los campos proporcionados
    for key, value in update_data.items():
        setattr(user, key, value)
    
    # Actualizar la fecha de modificación
    user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "update_failed",
                "message": f"Error al actualizar el usuario: {str(e)}"
            }
        )
