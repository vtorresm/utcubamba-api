from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from passlib.context import CryptContext
from .base import BaseModel, Role, UserStatus

# Contexto para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserBase(SQLModel):
    """Base model for User with common attributes."""
    nombre: str = Field(max_length=100, nullable=False)
    email: str = Field(max_length=255, unique=True, index=True, nullable=False)
    hashed_password: str = Field(max_length=255, nullable=False)
    cargo: str = Field(max_length=100, nullable=False)
    departamento: str = Field(max_length=100, nullable=False)
    contacto: Optional[str] = Field(
        default=None, 
        max_length=50, 
        index=True, 
        unique=True,
        nullable=True
    )  # Número de teléfono o extensión (único por usuario)
    fecha_ingreso: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    estado: UserStatus = Field(default=UserStatus.ACTIVO, nullable=False)
    role: Role = Field(default=Role.USER, nullable=False)

class User(UserBase, BaseModel, table=True):
    """User model for database."""
    __tablename__ = "users"
    
    # Relación con tokens de restablecimiento de contraseña
    password_reset_tokens: List["PasswordResetToken"] = Relationship(back_populates="user")
    
    # Métodos para el manejo de contraseñas
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing."""
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a stored password against one provided by user."""
        return pwd_context.verify(password, self.hashed_password)
    
    def desactivar_usuario(self):
        """Desactiva el usuario cambiando su estado."""
        self.estado = UserStatus.DADO_DE_BAJA
        self.updated_at = datetime.utcnow()

class UserCreate(SQLModel):
    """Model for creating a new user."""
    nombre: str
    email: str
    password: str
    cargo: str
    departamento: str
    contacto: Optional[str] = None
    role: Role = Role.USER

class UserUpdate(SQLModel):
    """Model for updating an existing user."""
    nombre: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    contacto: Optional[str] = None
    estado: Optional[UserStatus] = None
    role: Optional[Role] = None

class UserInDB(UserBase):
    """User model for returning user data (without sensitive info)."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Método para reactivar usuario
    def reactivar_usuario(self):
        self.estado = UserStatus.ACTIVO
    
    # Relación con los tokens de restablecimiento de contraseña
    password_reset_tokens: List["PasswordResetToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    # Representación en string
    def __repr__(self):
        return f"<User {self.email}>"