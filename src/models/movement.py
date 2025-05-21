from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .medication import Medication
    from .prediction import Prediction

class MovementType(str, Enum):
    IN = "in"
    OUT = "out"

class MovementBase(SQLModel):
    """Base model for Movement with common attributes."""
    date: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    type: MovementType = Field(..., description="Type of movement: 'in' for entry, 'out' for exit")
    quantity: float = Field(..., gt=0, description="Quantity of medication moved")
    notes: Optional[str] = Field(default=None, max_length=500)
    
    # Foreign keys
    medication_id: int = Field(foreign_key="medications.id")

class Movement(MovementBase, table=True):
    """Movement model for database."""
    __tablename__ = "movements"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Relationships
    medication: "Medication" = Relationship(back_populates="movements")
    prediction: Optional["Prediction"] = Relationship(back_populates="movement", sa_relationship_kwargs={"uselist": False})

class MovementCreate(MovementBase):
    """Model for creating a new movement."""
    pass

class MovementUpdate(SQLModel):
    """Model for updating an existing movement."""
    date: Optional[datetime] = None
    type: Optional[MovementType] = None
    quantity: Optional[float] = None
    notes: Optional[str] = None
    medication_id: Optional[int] = None

class MovementInDB(MovementBase):
    """Movement model for returning movement data."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
