from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .base import BaseModel

if TYPE_CHECKING:
    from .medication import Medication
    from .medication_condition import MedicationConditionLink

class ConditionBase(SQLModel):
    """Base model for Condition with common attributes."""
    name: str = Field(..., max_length=100, unique=True, nullable=False, index=True)
    description: Optional[str] = Field(default=None, max_length=500)

class Condition(ConditionBase, BaseModel, table=True):
    """Condition model for database."""
    __tablename__ = "conditions"
    
    # Relationship to the association table
    medication_links: List["MedicationConditionLink"] = Relationship(back_populates="condition")
    
    # Relationship to medications through the association table
    @property
    def medications(self) -> List["Medication"]:
        return [link.medication for link in self.medication_links]

    def __hash__(self):
        return hash(self.id) if self.id else 0

class ConditionCreate(ConditionBase):
    """Model for creating a new condition."""
    pass

class ConditionUpdate(SQLModel):
    """Model for updating an existing condition."""
    name: Optional[str] = None
    description: Optional[str] = None

class ConditionInDB(ConditionBase):
    """Condition model for returning condition data."""
    id: int
    created_at: datetime
    updated_at: datetime
