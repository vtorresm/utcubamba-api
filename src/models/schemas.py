from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List, Dict

# Esquemas existentes
class CategoriaBase(BaseModel):
    nombre: str = Field(..., max_length=50)

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    categoria_id: int

    class Config:
        orm_mode = True

class CondicionBase(BaseModel):
    nombre: str = Field(..., max_length=50)

class CondicionCreate(CondicionBase):
    pass

class Condicion(CondicionBase):
    condicion_id: int

    class Config:
        orm_mode = True

class TipoTomaBase(BaseModel):
    nombre: str = Field(..., max_length=50)

class TipoTomaCreate(TipoTomaBase):
    pass

class TipoToma(TipoTomaBase):
    tipo_toma_id: int

    class Config:
        orm_mode = True

class MedicamentoBase(BaseModel):
    nombre_comercial: str = Field(..., max_length=100)
    nombre_generico: Optional[str] = Field(None, max_length=100)
    presentacion: Optional[str] = Field(None, max_length=100)
    concentracion: Optional[str] = Field(None, max_length=50)
    laboratorio: Optional[str] = Field(None, max_length=100)
    precio_unitario: float = Field(..., gt=0)
    stock_actual: int = Field(..., ge=0)
    fecha_vencimiento: Optional[date] = None
    codigo_barras: Optional[str] = Field(None, max_length=50)
    requiere_receta: bool = False
    unidad_empaque: Optional[int] = None
    via_administracion: Optional[str] = Field(None, max_length=50)
    disponibilidad: str = Field(..., max_length=20)
    categoria_id: int
    condicion_id: int
    tipo_toma_id: int

class MedicamentoCreate(MedicamentoBase):
    pass

class Medicamento(MedicamentoBase):
    medicamento_id: int
    categoria: Categoria
    condicion: Condicion
    tipo_toma: TipoToma

    class Config:
        orm_mode = True

# Nuevos esquemas para el reporte
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
    encabezado: Dict[str, str]
    datos: List[ReporteInventarioItem]
    resumen: Dict[str, float]