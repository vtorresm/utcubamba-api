from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.services.auth_service import AuthService
from src.models.user import Role, User, UserStatus
from datetime import timedelta, datetime
import os
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from fastapi.responses import JSONResponse

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

logger = logging.getLogger(__name__)

router = APIRouter()

# Modelos para las solicitudes
class LoginRequest(BaseModel):
    username: str = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, max_length=100)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    exp: Optional[datetime] = None

class RegisterRequest(BaseModel):
    """Modelo para la solicitud de registro de usuario."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100, description="Nombre completo del usuario")
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Alias de nombre (compatibilidad con frontend)")
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, max_length=100, description="Contraseña con al menos 6 caracteres")
    cargo: Optional[str] = Field(default="", max_length=100, description="Cargo o puesto del usuario")
    departamento: Optional[str] = Field(default="", max_length=100, description="Departamento o área al que pertenece el usuario")
    contacto: Optional[str] = Field(
        None,
        min_length=8,
        max_length=50,
        description="Número de teléfono o extensión (opcional)",
        example="+51987654321"
    )
    role: Role = Field(
        default=Role.USER,
        description=f"Rol del usuario en el sistema. Valores permitidos: {', '.join([r.value for r in Role])}"
    )

    @validator('nombre', pre=True, always=True)
    def set_nombre_from_name(cls, v, values):
        return v or values.get('name') or ''

    @validator('role')
    def validate_role(cls, v):
        if v not in [r.value for r in Role]:
            raise ValueError(f"Rol inválido. Debe ser uno de: {', '.join([r.value for r in Role])}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Juan Pérez",
                "email": "juan.perez@gmail.com",
                "password": "miclave123",
                "role": "user"
            }
        }

class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Correo electrónico del usuario")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@utcubamba.edu.pe"
            }
        }

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)

@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    tags=["auth"],
    responses={
        200: {"description": "Inicio de sesión exitoso"},
        401: {"description": "Credenciales inválidas"},
        422: {"description": "Error de validación"}
    }
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Inicia sesión y devuelve un token JWT.

    - **username**: Email del usuario
    - **password**: Contraseña del usuario
    """
    try:
        logger.info("[AUTH] Intento de inicio de sesión")

        # Verificar el usuario
        user = AuthService.verify_user(db, request.username, request.password)
        if not user:
            logger.warning("[AUTH] Credenciales incorrectas para el usuario proporcionado")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_credentials", "message": "Credenciales incorrectas"}
            )

        logger.info(f"[AUTH] Usuario autenticado con rol: {user.role}")

        # Crear token de acceso
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "role": user.role,
                "status": user.estado.value if user.estado else None
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Error interno del servidor"}
        )

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    responses={
        201: {"description": "Usuario registrado exitosamente"},
        400: {"description": "Error en la solicitud"},
        422: {"description": "Error de validación"},
        500: {"description": "Error interno del servidor"}
    }
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Registra un nuevo usuario en el sistema con toda su información personal y laboral.

    - **nombre**: Nombre completo del usuario (requerido, 2-100 caracteres)
    - **email**: Email institucional (requerido, debe ser único)
    - **password**: Contraseña (requerido, mínimo 6 caracteres)
    - **cargo**: Cargo o puesto del usuario (requerido, 2-100 caracteres)
    - **departamento**: Departamento o área (requerido, 2-100 caracteres)
    - **contacto**: Número de teléfono o extensión (opcional, 8-50 caracteres)
    - **role**: Rol del usuario en el sistema (opcional, por defecto 'user')
    """
    try:
        # Registrar el nuevo usuario con todos los campos requeridos
        user = AuthService.register_user(
            db=db,
            email=request.email,
            password=request.password,
            nombre=request.nombre,
            cargo=request.cargo,
            departamento=request.departamento,
            contacto=request.contacto,
            role=request.role
        )

        # Generar token para auto-login tras el registro
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=access_token_expires
        )

        response_data = {
            "message": "Usuario registrado exitosamente",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "role": user.role,
                "status": user.estado.value if user.estado else None,
            }
        }

        return response_data

    except HTTPException as e:
        # Re-lanzar excepciones HTTP existentes
        raise e

    except Exception as e:
        # Manejar cualquier otro error inesperado
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "registration_failed",
                "message": "Error inesperado al registrar el usuario"
            }
        )

@router.post("/password-reset", tags=["auth"])
async def request_password_reset(
    request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Solicita un token para restablecer la contraseña.

    - **email**: Correo electrónico del usuario que desea restablecer la contraseña
    """
    from src.services.email_service import EmailService

    try:
        # Buscar usuario por email
        user = db.query(User).filter(User.email == request.email).first()

        # Si el usuario existe, generar token y enviar correo
        if user:
            token = AuthService.generate_reset_token(db, request.email)
            if token:
                await EmailService.send_password_reset_email(
                    background_tasks=background_tasks,
                    to_email=request.email,
                    token=token,
                    username=user.nombre or "Usuario"
                )

        # Por seguridad, siempre devolvemos el mismo mensaje
        return {
            "message": "Si tu correo está registrado, recibirás un enlace para restablecer tu contraseña"
        }
    except Exception as e:
        import logging
        logging.error(f"Error en password-reset: {str(e)}", exc_info=True)
        return {
            "message": "Si tu correo está registrado, recibirás un enlace para restablecer tu contraseña"
        }

@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_200_OK,
    tags=["auth"],
    responses={
        200: {"description": "Contraseña restablecida exitosamente"},
        400: {"description": "Token inválido o expirado"},
        422: {"description": "Error de validación"}
    }
)
async def reset_password(
    request: ResetPasswordConfirm,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Restablece la contraseña usando un token de restablecimiento.

    - **token**: Token de restablecimiento de contraseña
    - **new_password**: Nueva contraseña (mínimo 6 caracteres)
    """
    try:
        AuthService.reset_password(db, request.token, request.new_password)
        return {
            "message": "Contraseña restablecida exitosamente"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "reset_failed", "message": "No se pudo restablecer la contraseña"}
        )