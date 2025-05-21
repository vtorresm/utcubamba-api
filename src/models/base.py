from datetime import datetime
from typing import Optional, List, TypeVar, Generic, Type, Any
from enum import Enum
from pydantic import BaseModel as PydanticBaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, Relationship

# Hacer que passlib sea opcional para las migraciones
try:
    from passlib.context import CryptContext
    # Contexto para encriptar contraseñas
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    HAS_PASSLIB = True
except ImportError:
    pwd_context = None
    HAS_PASSLIB = False

# Tipos de datos personalizados
class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    FARMACIA = "farmacia"
    ENFERMERIA = "enfermeria"

class UserStatus(str, Enum):
    ACTIVO = "activo"
    DADO_DE_BAJA = "dado_de_baja"

# Clase base para SQLModel
class Base(SQLModel):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    created_at: datetime = SQLField(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow, nullable=False)

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

# Alias para compatibilidad
BaseModel = Base
