from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class MedicationBase(BaseModel):
    """Base model for Medication with common attributes."""
    name: str
    description: Optional[str] = None
    stock: int
    min_stock: int
    unit: str
    manufacturer: Optional[str] = None
    expiration_date: Optional[datetime] = None
    status: str
    price: float
    category_id: Optional[int] = None
    intake_type_id: Optional[int] = None

class MedicationCreate(MedicationBase):
    """Model for creating a new medication."""
    condition_ids: List[int] = Field(default_factory=list)

class MedicationUpdate(BaseModel):
    """Model for updating an existing medication."""
    name: Optional[str] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    min_stock: Optional[int] = None
    unit: Optional[str] = None
    manufacturer: Optional[str] = None
    expiration_date: Optional[datetime] = None
    status: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    intake_type_id: Optional[int] = None
    condition_ids: Optional[List[int]] = None

class CategoryResponse(BaseModel):
    """Response model for Category in Medication response."""
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class MedicationResponse(MedicationBase):
    """Response model for Medication."""
    id: int
    created_at: datetime
    updated_at: datetime
    condition_ids: List[int] = Field(default_factory=list)
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True