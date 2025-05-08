from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from src.db.database import Base
import enum

class TipoMovimiento(enum.Enum):
    ENTRADA = "Entrada"
    SALIDA = "Salida"

class Categoria(Base):
    __tablename__ = "categorias"

    categoria_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    medicamentos = relationship("Medicamento", back_populates="categoria")

class Condicion(Base):
    __tablename__ = "condiciones"

    condicion_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    medicamentos = relationship("Medicamento", back_populates="condicion")

class TipoToma(Base):
    __tablename__ = "tipos_toma"

    tipo_toma_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    medicamentos = relationship("Medicamento", back_populates="tipo_toma")

class Medicamento(Base):
    __tablename__ = "medicamentos"

    medicamento_id = Column(Integer, primary_key=True, index=True)
    nombre_comercial = Column(String(100), nullable=False)
    nombre_generico = Column(String(100))
    presentacion = Column(String(100))
    concentracion = Column(String(50))
    laboratorio = Column(String(100))
    precio_unitario = Column(Float, nullable=False)
    stock_actual = Column(Integer, nullable=False)
    fecha_vencimiento = Column(Date)
    codigo_barras = Column(String(50), unique=True)
    requiere_receta = Column(Boolean, default=False)
    unidad_empaque = Column(Integer)
    via_administracion = Column(String(50))
    disponibilidad = Column(String(20), nullable=False, default="En Stock")
    categoria_id = Column(Integer, ForeignKey("categorias.categoria_id"), nullable=False)
    condicion_id = Column(Integer, ForeignKey("condiciones.condicion_id"), nullable=False)
    tipo_toma_id = Column(Integer, ForeignKey("tipos_toma.tipo_toma_id"), nullable=False)

    categoria = relationship("Categoria", back_populates="medicamentos")
    condicion = relationship("Condicion", back_populates="medicamentos")
    tipo_toma = relationship("TipoToma", back_populates="medicamentos")
    movimientos = relationship("Movimiento", back_populates="medicamento")

class Movimiento(Base):
    __tablename__ = "movimientos"

    movimiento_id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False)
    tipo_movimiento = Column(Enum(TipoMovimiento), nullable=False)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.medicamento_id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    observaciones = Column(String(200))

    medicamento = relationship("Medicamento", back_populates="movimientos")