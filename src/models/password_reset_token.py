from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from .base import BaseModel

class PasswordResetTokenBase(SQLModel):
    """Base model for PasswordResetToken with common attributes."""
    token: str = Field(..., max_length=255, unique=True, nullable=False)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=1),
        nullable=False
    )

class PasswordResetToken(PasswordResetTokenBase, BaseModel, table=True):
    """
    Modelo para almacenar tokens de restablecimiento de contraseña.
    
    Atributos:
        id (int): Identificador único del token.
        user_id (int): ID del usuario al que pertenece el token.
        token (str): Token único para el restablecimiento de contraseña.
        created_at (datetime): Fecha y hora de creación del token.
        expires_at (datetime): Fecha y hora de expiración del token.
    """
    __tablename__ = "password_reset_tokens"
    
    # Relación con el usuario
    user_id: int = Field(foreign_key="users.id", nullable=False)
    user: "User" = Relationship(back_populates="password_reset_tokens")
    
    def is_expired(self) -> bool:
        """Verifica si el token ha expirado."""
        return datetime.utcnow() > self.expires_at

class PasswordResetTokenCreate(SQLModel):
    """Model for creating a new password reset token."""
    email: str

class PasswordResetTokenResponse(PasswordResetTokenBase):
    """Response model for password reset token."""
    id: int
    user_id: int
    created_at: datetime

class PasswordResetRequest(SQLModel):
    """Model for password reset request."""
    token: str
    new_password: str