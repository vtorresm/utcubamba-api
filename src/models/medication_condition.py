from sqlmodel import SQLModel, Field, Relationship
from .base import BaseModel

class MedicationConditionLink(BaseModel, table=True):
    """Association table for many-to-many relationship between Medication and Condition."""
    __tablename__ = "medication_condition"
    
    # Primary key
    id: int = Field(default=None, primary_key=True, index=True)
    
    # Foreign keys
    medication_id: int = Field(
        default=None,
        foreign_key="medications.id",
        nullable=False,
        index=True
    )
    condition_id: int = Field(
        default=None,
        foreign_key="conditions.id",
        nullable=False,
        index=True
    )
    
    # Relationships
    medication: "Medication" = Relationship(back_populates="condition_links")
    condition: "Condition" = Relationship(back_populates="medication_links")
    
    # Add a unique constraint on the combination of medication_id and condition_id
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
