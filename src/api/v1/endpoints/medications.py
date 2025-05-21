from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

from src.core.database import get_db
from src.models.user import User, Role
from src.dependencies.auth import get_current_user

router = APIRouter()

# Pydantic models for request/response
class MedicationBase(BaseModel):
    name: str
    description: Optional[str] = None
    stock: int = 0
    category_id: Optional[int] = None
    intake_type_id: Optional[int] = None
    expiration_date: Optional[date] = None
    price: Optional[float] = None
    
    class Config:
        from_attributes = True

class MedicationCreate(MedicationBase):
    pass

class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    intake_type_id: Optional[int] = None
    expiration_date: Optional[date] = None
    price: Optional[float] = None
    
    class Config:
        from_attributes = True

class MedicationResponse(MedicationBase):
    id: int
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    
    class Config:
        from_attributes = True

# Get all medications
@router.get("/", response_model=List[MedicationResponse])
def get_medications(
    skip: int = 0, 
    limit: int = 100,
    name: Optional[str] = None,
    category_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all medications with optional filtering.
    """
    # TODO: Replace with actual Medication model import
    from src.models import Medication
    
    query = db.query(Medication)
    
    # Apply filters if provided
    if name:
        query = query.filter(Medication.name.ilike(f'%{name}%'))
    if category_id:
        query = query.filter(Medication.category_id == category_id)
    
    medications = query.offset(skip).limit(limit).all()
    return medications

# Get specific medication by ID
@router.get("/{medication_id}", response_model=MedicationResponse)
def get_medication(
    medication_id: int = Path(..., description="ID of the medication"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific medication by ID.
    """
    # TODO: Replace with actual Medication model import
    from src.models import Medication
    
    medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    return medication

# Create new medication
@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
def create_medication(
    medication: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new medication.
    """
    # Check if user has admin permissions
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # TODO: Replace with actual Medication model import
    # For now, using a mock implementation for testing
    from src.models import Medication
    
    # Create new medication
    db_medication = Medication(**medication.model_dump())
    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)
    return db_medication

# Update medication
@router.put("/{medication_id}", response_model=MedicationResponse)
def update_medication(
    medication_id: int,
    medication: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing medication.
    """
    # Check if user has admin permissions
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # TODO: Replace with actual Medication model import
    from src.models import Medication
    
    # Get the medication
    db_medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if db_medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    # Update medication fields
    medication_data = medication.model_dump(exclude_unset=True)
    for key, value in medication_data.items():
        setattr(db_medication, key, value)
    
    db.commit()
    db.refresh(db_medication)
    return db_medication

# Delete medication
@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a medication.
    """
    # Check if user has admin permissions
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # TODO: Replace with actual Medication model import
    from src.models import Medication
    
    # Get the medication
    db_medication = db.query(Medication).filter(Medication.id == medication_id).first()
    if db_medication is None:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    # Delete the medication
    db.delete(db_medication)
    db.commit()
    return None

