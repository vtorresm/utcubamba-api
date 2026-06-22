from typing import TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .medication import Medication
    from .condition import Condition


class MedicationConditionLink(SQLModel, table=True):
    """Tabla asociativa many-to-many entre Medication y Condition.

    Usa clave primaria compuesta (medication_id + condition_id) — sin columna
    id autoincrementada — que es el patron correcto para tablas de union en
    PostgreSQL con SQLModel.
    """
    __tablename__ = "medication_condition"

    medication_id: int = Field(foreign_key="medications.id", primary_key=True)
    condition_id: int  = Field(foreign_key="conditions.id",  primary_key=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    medication: "Medication" = Relationship(back_populates="condition_links")
    condition:  "Condition"  = Relationship(back_populates="medication_links")
