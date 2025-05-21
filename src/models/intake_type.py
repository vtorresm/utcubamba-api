from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from .medication import Medication

class IntakeTypeBase(SQLModel):
    """Base model for IntakeType with common attributes."""
    name: str = Field(..., max_length=100, unique=True, nullable=False, index=True)
    description: Optional[str] = Field(default=None, max_length=500)

class IntakeType(IntakeTypeBase, table=True):
    """IntakeType model for database."""
    __tablename__ = "intake_types"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Relationships
    medications: List["Medication"] = Relationship(back_populates="intake_type")

class IntakeTypeCreate(IntakeTypeBase):
    """Model for creating a new intake type."""
    pass

class IntakeTypeUpdate(SQLModel):
    """Model for updating an existing intake type."""
    name: Optional[str] = None
    description: Optional[str] = None

class IntakeTypeInDB(IntakeTypeBase):
    """IntakeType model for returning intake type data."""
    id: int
    created_at: datetime
    updated_at: datetime
