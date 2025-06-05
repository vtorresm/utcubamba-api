from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CategoryBase(BaseModel):
    """Base model for Category with common attributes."""
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    """Model for creating a new category."""
    pass

class CategoryUpdate(BaseModel):
    """Model for updating an existing category."""
    name: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    """Response model for Category."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
