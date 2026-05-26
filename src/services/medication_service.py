from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
import logging

from src.models.medication import Medication, MedicationCreate, MedicationUpdate
from src.models.category import Category
from src.models.intake_type import IntakeType
from src.models.condition import Condition
from src.models.medication_condition import MedicationConditionLink

logger = logging.getLogger(__name__)


def get_medications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    category_id: Optional[int] = None,
    intake_type_id: Optional[int] = None
) -> List[Medication]:
    query = db.query(Medication).options(
        joinedload(Medication.category),
        joinedload(Medication.intake_type)
    )
    if name:
        query = query.filter(Medication.name.ilike(f'%{name}%'))
    if category_id is not None:
        query = query.filter(Medication.category_id == category_id)
    if intake_type_id is not None:
        query = query.filter(Medication.intake_type_id == intake_type_id)
    return query.offset(skip).limit(limit).all()


def get_medication_by_id(db: Session, medication_id: int) -> Optional[Medication]:
    return db.get(Medication, medication_id)


def create_medication(db: Session, medication_data: MedicationCreate) -> Medication:
    if medication_data.category_id is not None:
        category = db.get(Category, medication_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {medication_data.category_id} not found"
            )
    if medication_data.intake_type_id is not None:
        intake_type = db.get(IntakeType, medication_data.intake_type_id)
        if not intake_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intake type with id {medication_data.intake_type_id} not found"
            )

    medication_data_dict = medication_data.model_dump(exclude={"condition_ids"})
    db_medication = Medication(**medication_data_dict)

    if medication_data.condition_ids:
        for condition_id in medication_data.condition_ids:
            condition = db.get(Condition, condition_id)
            if condition:
                db_medication.condition_links.append(
                    MedicationConditionLink(condition=condition)
                )

    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)
    return db_medication


def update_medication(db: Session, medication_id: int, update_data: MedicationUpdate) -> Optional[Medication]:
    db_medication = db.get(Medication, medication_id)
    if not db_medication:
        return None

    update_dict = update_data.model_dump(exclude_unset=True, exclude={"condition_ids"})
    for key, value in update_dict.items():
        if hasattr(db_medication, key):
            setattr(db_medication, key, value)

    if hasattr(update_data, 'condition_ids') and update_data.condition_ids is not None:
        db_medication.condition_links.clear()
        for condition_id in update_data.condition_ids:
            condition = db.get(Condition, condition_id)
            if condition:
                db_medication.condition_links.append(
                    MedicationConditionLink(condition=condition)
                )

    db.commit()
    db.refresh(db_medication)
    return db_medication


def delete_medication(db: Session, medication_id: int) -> bool:
    db_medication = db.get(Medication, medication_id)
    if not db_medication:
        return False
    db.delete(db_medication)
    db.commit()
    return True


def get_medications_count(db: Session) -> int:
    return db.query(Medication).count()


def get_low_stock_medications(db: Session, skip: int = 0, limit: int = 50) -> List[Medication]:
    return db.query(Medication).filter(
        Medication.stock <= Medication.min_stock
    ).offset(skip).limit(limit).all()
