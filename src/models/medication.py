from typing import List, Optional, TYPE_CHECKING, Set
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from .base import BaseModel

# Importaciones condicionales para evitar importaciones circulares
if TYPE_CHECKING:
    from .category import Category
    from .condition import Condition
    from .intake_type import IntakeType
    from .movement import Movement
    from .prediction import Prediction
    from .medication_condition import MedicationConditionLink

class MedicationBase(SQLModel):
    """Base model for Medication with common attributes."""
    name: str = Field(..., max_length=100, nullable=False, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    stock: int = Field(default=0, ge=0, description="Current stock quantity")
    min_stock: int = Field(default=10, ge=0, description="Minimum stock level before alert")
    unit: str = Field(default="units", max_length=50, description="Measurement unit (e.g., 'mg', 'ml', 'units')")
    manufacturer: Optional[str] = Field(default=None, max_length=200, description="Fabricante del medicamento")
    expiration_date: Optional[datetime] = Field(
        default=None, 
        description="Fecha de vencimiento del lote actual"
    )
    status: str = Field(
        default="Activo",
        max_length=50,
        description="Estado del medicamento (Activo, Inactivo, Vencido, Retirado)"
    )
    price: float = Field(
        default=0.0,
        ge=0,
        description="Precio unitario del medicamento"
    )
    
    # Foreign keys
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    intake_type_id: Optional[int] = Field(default=None, foreign_key="intake_types.id")

class Medication(MedicationBase, BaseModel, table=True):
    """Medication model for database."""
    __tablename__ = "medications"
    
    # Relationships
    category: Optional["Category"] = Relationship(back_populates="medications")
    intake_type: Optional["IntakeType"] = Relationship(back_populates="medications")
    
    # Relationship to the association table
    condition_links: List["MedicationConditionLink"] = Relationship(back_populates="medication")
    
    # Relationship to conditions through the association table
    @property
    def conditions(self) -> List["Condition"]:
        return [link.condition for link in self.condition_links]
    
    # One-to-many relationship with Movement
    movements: List["Movement"] = Relationship(back_populates="medication")
    
    # One-to-many relationship with Prediction
    predictions: List["Prediction"] = Relationship(back_populates="medication")

class MedicationCreate(MedicationBase):
    """Model for creating a new medication."""
    condition_ids: Optional[List[int]] = Field(
        default_factory=list, 
        description="List of condition IDs associated with this medication"
    )
    manufacturer: Optional[str] = None
    expiration_date: Optional[datetime] = None
    status: Optional[str] = "Activo"
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Precio unitario del medicamento"
    )

class MedicationUpdate(SQLModel):
    """Model for updating an existing medication."""
    name: Optional[str] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    min_stock: Optional[int] = None
    unit: Optional[str] = None
    manufacturer: Optional[str] = None
    expiration_date: Optional[datetime] = None
    status: Optional[str] = None
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Precio unitario del medicamento"
    )
    category_id: Optional[int] = None
    intake_type_id: Optional[int] = None
    condition_ids: Optional[List[int]] = None

class MedicationInDB(MedicationBase):
    """Medication model for returning medication data."""
    id: int
    created_at: datetime
    updated_at: datetime
    condition_ids: List[int] = Field(default_factory=list)
    
    class Config:
        from_attributes = True