from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from src.db.database import Base
import enum
from datetime import datetime

class TipoMovimiento(enum.Enum):
    Entrada = "Entrada"
    Salida = "Salida"

class Categoria(Base):
    __tablename__ = "categorias"
    categoria_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)
    medicamentos = relationship("Medicamento", back_populates="categoria")

class Condicion(Base):
    __tablename__ = "condiciones"
    condicion_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)
    medicamentos = relationship("Medicamento", back_populates="condicion")

class TipoToma(Base):
    __tablename__ = "tipos_toma"
    tipo_toma_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)
    medicamentos = relationship("Medicamento", back_populates="tipo_toma")

class Medicamento(Base):
    __tablename__ = "medicamentos"
    medicamento_id = Column(Integer, primary_key=True, index=True)
    nombre_comercial = Column(String, nullable=False)
    nombre_generico = Column(String, nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.categoria_id"), nullable=False)
    stock_actual = Column(Integer, nullable=False, default=0)
    stock_maximo = Column(Integer, nullable=True)  # Nuevo campo
    precio_unitario = Column(Float, nullable=False)
    disponibilidad = Column(String, nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=True)
    lote = Column(String, nullable=True)
    laboratorio = Column(String, nullable=True)
    requiere_receta = Column(String, nullable=True)
    condicion_id = Column(Integer, ForeignKey("condiciones.condicion_id"), nullable=True)
    tipo_toma_id = Column(Integer, ForeignKey("tipos_toma.tipo_toma_id"), nullable=True)
    categoria = relationship("Categoria", back_populates="medicamentos")
    condicion = relationship("Condicion", back_populates="medicamentos")
    tipo_toma = relationship("TipoToma", back_populates="medicamentos")
    movimientos = relationship("Movimiento", back_populates="medicamento")
    alertas = relationship("Alerta", back_populates="medicamento")

class Movimiento(Base):
    __tablename__ = "movimientos"
    movimiento_id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    tipo_movimiento = Column(Enum(TipoMovimiento), nullable=False)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.medicamento_id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    observaciones = Column(String, nullable=True)
    medicamento = relationship("Medicamento", back_populates="movimientos")

# Nueva tabla: AlertaModel
class EstadoAlerta(enum.Enum):
    Pendiente = "Pendiente"
    Resuelta = "Resuelta"

class Alerta(Base):
    __tablename__ = "alertas"
    alerta_id = Column(Integer, primary_key=True, index=True)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.medicamento_id"), nullable=False)
    tipo_alerta = Column(String, nullable=False, default="Stock bajo")  # Ejemplo: "Stock bajo"
    estado = Column(Enum(EstadoAlerta), nullable=False, default=EstadoAlerta.Pendiente)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    medicamento = relationship("Medicamento", back_populates="alertas")
    historial = relationship("HistorialAlerta", back_populates="alerta")

# Nueva tabla: HistorialAlertaModel
class AccionHistorial(enum.Enum):
    Creada = "Creada"
    Actualizada = "Actualizada"
    Resuelta = "Resuelta"
    Eliminada = "Eliminada"

class HistorialAlerta(Base):
    __tablename__ = "historial_alertas"
    historial_id = Column(Integer, primary_key=True, index=True)
    alerta_id = Column(Integer, ForeignKey("alertas.alerta_id"), nullable=False)
    accion = Column(Enum(AccionHistorial), nullable=False)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    observaciones = Column(Text, nullable=True)
    alerta = relationship("Alerta", back_populates="historial")

# Nueva tabla: UsoHistoricoModel
class UsoHistorico(Base):
    __tablename__ = "uso_historico"
    historico_id = Column(Integer, primary_key=True, index=True)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.medicamento_id"), nullable=False)
    mes = Column(Integer, nullable=False)
    anio = Column(Integer, nullable=False)
    region = Column(String, nullable=False)
    temporada = Column(String, nullable=False)
    uso_previsto = Column(Integer, nullable=False)
    uso_real = Column(Integer, nullable=False)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)
    medicamento = relationship("Medicamento", back_populates="uso_historico")

# Nueva tabla: PrediccionModel
class Prediccion(Base):
    __tablename__ = "predicciones"
    prediccion_id = Column(Integer, primary_key=True, index=True)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.medicamento_id"), nullable=False)
    mes = Column(Integer, nullable=False)
    anio = Column(Integer, nullable=False)
    region = Column(String, nullable=False)
    temporada = Column(String, nullable=False)
    uso_previsto = Column(Integer, nullable=False)
    uso_predicho = Column(Float, nullable=False)
    fecha_prediccion = Column(DateTime, nullable=False, default=datetime.utcnow)
    medicamento = relationship("Medicamento", back_populates="predicciones")

# Actualizar Medicamento
Medicamento.uso_historico = relationship("UsoHistorico", back_populates="medicamento")
Medicamento.predicciones = relationship("Prediccion", back_populates="medicamento")

# Modelo para User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

# Modelo para RefreshToken
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)