from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional
from datetime import datetime, date
import re
from src.core.config import ALLOWED_ROLES

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "user"

    @validator("name")
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters long")
        if len(v) > 50:
            raise ValueError("Name cannot exceed 50 characters")
        if not re.match(r"^[a-zA-ZÀ-ÿ]+(?:\s[a-zA-ZÀ-ÿ]+)*$", v):
            raise ValueError("Name can only contain letters and single spaces")
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)", v):
            raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, and one number")
        return v

    @validator("role")
    def validate_role(cls, v):
        if v not in ALLOWED_ROLES:
            raise ValueError(f"Role must be one of {', '.join(ALLOWED_ROLES)}")
        return v

class User(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenInfo(BaseModel):
    id: int
    token: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

class MedicamentoBase(BaseModel):
    nombre_comercial: str
    nombre_generico: str
    presentacion: str
    concentracion: str
    laboratorio: str
    precio_unitario: float = Field(..., gt=0)
    stock_actual: int = Field(..., ge=0)
    fecha_vencimiento: date
    codigo_barras: Optional[str] = None
    requiere_receta: bool = False
    unidad_empaque: int = Field(..., gt=0)
    via_administracion: str

class MedicamentoCreate(MedicamentoBase):
    @validator("nombre_comercial", "nombre_generico", "laboratorio")
    def validate_text_fields(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        if len(v) > 255:
            raise ValueError("Field cannot exceed 255 characters")
        return v

    @validator("presentacion", "concentracion", "via_administracion")
    def validate_short_text(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        if len(v) > 100:
            raise ValueError("Field cannot exceed 100 characters")
        return v

    @validator("codigo_barras")
    def validate_codigo_barras(cls, v):
        if v and len(v) > 50:
            raise ValueError("Barcode cannot exceed 50 characters")
        if v and not v.isalnum():
            raise ValueError("Barcode must be alphanumeric")
        return v

class Medicamento(MedicamentoBase):
    medicamento_id: int

    class Config:
        from_attributes = True