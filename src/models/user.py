from sqlalchemy import Column, Integer, String, Enum, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database import Base
from passlib.context import CryptContext
import enum
from typing import List
from .password_reset_token import PasswordResetToken

# Definir los roles como un Enum
class Role(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    FARMACIA = "farmacia"
    ENFERMERIA = "enfermeria"

# Estados de usuario
class UserStatus(str, enum.Enum):
    ACTIVO = "activo"
    DADO_DE_BAJA = "dado_de_baja"

# Contexto para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    cargo = Column(String(100), nullable=False)
    departamento = Column(String(100), nullable=False)
    contacto = Column(String(50), nullable=True)  # Número de teléfono o extensión
    fecha_ingreso = Column(Date, default=datetime.utcnow, nullable=False)
    estado = Column(Enum(UserStatus), default=UserStatus.ACTIVO, nullable=False)
    role = Column(Enum(Role), default=Role.USER, nullable=False)
    
    # Métodos para el manejo de contraseñas
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)
    
    # Método para desactivar usuario
    def desactivar_usuario(self):
        self.estado = UserStatus.DADO_DE_BAJA
    
    # Método para reactivar usuario
    def reactivar_usuario(self):
        self.estado = UserStatus.ACTIVO
    
    # Relación con los tokens de restablecimiento de contraseña
    password_reset_tokens = relationship(
        "PasswordResetToken", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Representación en string
    def __repr__(self):
        return f"<User {self.email}>"