from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from .medication import Medication

class CategoryBase(SQLModel):
    """Base model for Category with common attributes."""
    name: str = Field(..., max_length=100, unique=True, nullable=False, index=True)
    description: Optional[str] = Field(default=None, max_length=500)

class Category(CategoryBase, table=True):
    """Category model for database."""
    __tablename__ = "categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Relationships
    medications: List["Medication"] = Relationship(back_populates="category")

class CategoryCreate(CategoryBase):
    """Model for creating a new category."""
    pass

class CategoryUpdate(SQLModel):
    """Model for updating an existing category."""
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryInDB(CategoryBase):
    """Category model for returning category data."""
    id: int
    created_at: datetime
    updated_at: datetime
