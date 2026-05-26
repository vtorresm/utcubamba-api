from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from src.models.user import Role, UserStatus


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    contacto: Optional[str] = None
    role: Optional[Role] = None
    estado: Optional[UserStatus] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def model_dump(self, **kwargs):
        exclude_none = kwargs.pop("exclude_none", False)
        result = super().model_dump(**kwargs)
        if exclude_none:
            return {k: v for k, v in result.items() if v is not None}
        return result


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    contacto: Optional[str] = None
    estado: Optional[UserStatus] = None
    role: Optional[Role] = None


class UserResponse(UserBase):
    id: int
    fecha_ingreso: Optional[datetime] = None
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
