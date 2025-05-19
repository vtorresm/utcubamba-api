from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.core.database import Base
from datetime import datetime, timedelta

class PasswordResetToken(Base):
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
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relación con el usuario
    user = relationship("User", back_populates="password_reset_tokens")
    
    def __init__(self, **kwargs):
        # Establecer la fecha de expiración por defecto a 1 hora desde la creación
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.utcnow() + timedelta(hours=1)
        super().__init__(**kwargs)
    
    def is_expired(self) -> bool:
        """Verifica si el token ha expirado."""
        return datetime.utcnow() > self.expires_at