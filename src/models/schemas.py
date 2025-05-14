from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# Authentication schemas
class TokenData(BaseModel):
    email: str
    role: str

class LoginRequest(BaseModel):
    username: EmailStr
    password: str

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: Optional[dict] = None

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: User

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenInfo(BaseModel):
    id: int
    token: str
    user_id: int
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

class TipoMovimiento(str, Enum):
    Entrada = "Entrada"
    Salida = "Salida"

class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    categoria_id: int
    class Config:
        from_attributes = True

class CondicionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class CondicionCreate(CondicionBase):
    pass

class Condicion(CondicionBase):
    condicion_id: int
    class Config:
        from_attributes = True

class TipoTomaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class TipoTomaCreate(TipoTomaBase):
    pass

class TipoToma(TipoTomaBase):
    tipo_toma_id: int
    class Config:
        from_attributes = True

class MedicamentoBase(BaseModel):
    nombre_comercial: str
    nombre_generico: Optional[str] = None
    categoria_id: int
    stock_actual: int = 0
    stock_maximo: Optional[int] = None  # Nuevo campo
    precio_unitario: float
    disponibilidad: str
    fecha_vencimiento: Optional[datetime] = None
    lote: Optional[str] = None
    laboratorio: Optional[str] = None
    requiere_receta: Optional[str] = None
    condicion_id: Optional[int] = None
    tipo_toma_id: Optional[int] = None

class MedicamentoCreate(MedicamentoBase):
    pass

class Medicamento(MedicamentoBase):
    medicamento_id: int
    categoria: Categoria
    condicion: Optional[Condicion] = None
    tipo_toma: Optional[TipoToma] = None
    
    class Config:
        from_attributes = True

class MovimientoBase(BaseModel):
    fecha: datetime
    tipo_movimiento: TipoMovimiento
    medicamento_id: int
    cantidad: int
    observaciones: Optional[str] = None

class MovimientoCreate(BaseModel):
    tipo_movimiento: TipoMovimiento
    medicamento_id: int
    cantidad: int
    observaciones: Optional[str] = None

class Movimiento(MovimientoBase):
    movimiento_id: int
    class Config:
        from_attributes = True

class ReporteInventarioItem(BaseModel):
    id: int
    nombre_comercial: str
    nombre_generico: Optional[str]
    categoria: str
    stock: int
    precio_unitario: float
    valor_total: float
    estado: str

class ReporteInventario(BaseModel):
    encabezado: dict
    datos: List[ReporteInventarioItem]
    resumen: dict

class ReporteMovimientosItem(BaseModel):
    id: int
    fecha: datetime
    tipo_movimiento: str
    medicamento: str
    cantidad: int
    observaciones: Optional[str]

class ReporteMovimientos(BaseModel):
    encabezado: dict
    datos: List[ReporteMovimientosItem]
    resumen: dict

# Nuevos esquemas para Alerta y HistorialAlerta
class EstadoAlerta(str, Enum):
    Pendiente = "Pendiente"
    Resuelta = "Resuelta"

class AlertaBase(BaseModel):
    medicamento_id: int
    tipo_alerta: str = "Stock bajo"
    estado: EstadoAlerta = EstadoAlerta.Pendiente

class AlertaCreate(AlertaBase):
    pass

class AlertaUpdate(BaseModel):
    estado: EstadoAlerta
    observaciones: Optional[str] = None

class Alerta(AlertaBase):
    alerta_id: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    class Config:
        from_attributes = True

class AccionHistorial(str, Enum):
    Creada = "Creada"
    Actualizada = "Actualizada"
    Resuelta = "Resuelta"
    Eliminada = "Eliminada"

class HistorialAlertaBase(BaseModel):
    alerta_id: int
    accion: AccionHistorial
    observaciones: Optional[str] = None

class HistorialAlertaCreate(HistorialAlertaBase):
    pass

class HistorialAlerta(HistorialAlertaBase):
    historial_id: int
    fecha: datetime
    class Config:
        from_attributes = True

class UsoHistoricoBase(BaseModel):
    medicamento_id: int
    mes: int
    anio: int
    region: str
    temporada: str
    uso_previsto: int
    uso_real: int

class UsoHistoricoCreate(UsoHistoricoBase):
    pass

class UsoHistorico(UsoHistoricoBase):
    historico_id: int
    fecha_registro: datetime
    class Config:
        from_attributes = True

class PrediccionBase(BaseModel):
    medicamento_id: int
    mes: int
    anio: int
    region: str
    temporada: str
    uso_previsto: int
    uso_predicho: float

class PrediccionCreate(PrediccionBase):
    pass

class Prediccion(PrediccionBase):
    prediccion_id: int
    fecha_prediccion: datetime
    class Config:
        from_attributes = True