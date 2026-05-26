from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from src.models.user import Role, UserStatus


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    contacto: Optional[str] = None
    role: Optional[str] = None
    estado: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def model_dump(self, **kwargs):
        return {k: v for k, v in super().model_dump(**kwargs).items() if v is not None}


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    contacto: Optional[str] = None
    estado: Optional[UserStatus] = None
    role: Optional[Role] = None


class UserResponse(UserBase):
    id: int
    fecha_ingreso: Optional[datetime] = None
    estado: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
