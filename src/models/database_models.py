from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="refresh_tokens")

class Medicamento(Base):
    __tablename__ = "medicamentos"
    medicamento_id = Column(Integer, primary_key=True)
    nombre_comercial = Column(String(255), nullable=False)
    nombre_generico = Column(String(255), nullable=False)
    presentacion = Column(String(100), nullable=False)
    concentracion = Column(String(100), nullable=False)
    laboratorio = Column(String(255), nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    stock_actual = Column(Integer, nullable=False)
    fecha_vencimiento = Column(Date, nullable=False)
    codigo_barras = Column(String(50), unique=True, nullable=True)
    requiere_receta = Column(Boolean, nullable=False, default=False)
    unidad_empaque = Column(Integer, nullable=False)
    via_administracion = Column(String(100), nullable=False)