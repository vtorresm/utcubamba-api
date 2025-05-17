from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.core.database import Base

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    medicamentos = relationship("Medicamento", back_populates="categoria")

class Condicion(Base):
    __tablename__ = "condiciones"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    medicamentos = relationship("Medicamento", secondary="medicamento_condicion", back_populates="condiciones")

class TipoDeToma(Base):
    __tablename__ = "tipos_de_toma"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)

class Medicamento(Base):
    __tablename__ = "medicamentos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    categoria = relationship("Categoria", back_populates="medicamentos")
    condiciones = relationship("Condicion", secondary="medicamento_condicion")
    tipo_toma_id = Column(Integer, ForeignKey("tipos_de_toma.id"))

class MedicamentoCondicion(Base):
    __tablename__ = "medicamento_condicion"
    medicamento_id = Column(Integer, ForeignKey("medicamentos.id"), primary_key=True)
    condicion_id = Column(Integer, ForeignKey("condiciones.id"), primary_key=True)

class Movimiento(Base):
    __tablename__ = "movimientos"
    id = Column(Integer, primary_key=True, index=True)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.id"))
    fecha = Column(DateTime, nullable=False)
    tipo = Column(String(50), nullable=False)  # "entrada" o "salida"
    cantidad = Column(Float, nullable=False)
    predictions = relationship("Prediction", back_populates="movimiento")