# src/models/__init__.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, Table
from sqlalchemy.orm import relationship
from src.core.database import Base
import enum

# Association table for many-to-many relationship between Medication and Condition
medication_condition = Table(
    "medication_condition",
    Base.metadata,
    Column("medication_id", Integer, ForeignKey("medications.id"), primary_key=True),
    Column("condition_id", Integer, ForeignKey("conditions.id"), primary_key=True)
)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    medications = relationship("Medication", back_populates="category")

class Condition(Base):
    __tablename__ = "conditions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    medications = relationship(
        "Medication", 
        secondary=medication_condition, 
        back_populates="conditions"
    )

class IntakeType(Base):
    __tablename__ = "intake_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="medications")
    conditions = relationship(
        "Condition", 
        secondary=medication_condition,
        back_populates="medications"
    )
    intake_type_id = Column(Integer, ForeignKey("intake_types.id"))
    intake_type = relationship("IntakeType")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"))
    date = Column(DateTime, nullable=False)
    type = Column(String(50), nullable=False)  # "in" or "out"
    quantity = Column(Float, nullable=False)
    medication = relationship("Medication")
    predictions = relationship("Prediction", back_populates="movement")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"))
    medication = relationship("Medication")
    date = Column(DateTime, nullable=False)
    real_usage = Column(Float, nullable=False)  # Actual usage (R_i)
    predicted_usage = Column(Float, nullable=False)  # Predicted usage (P_i)
    stock = Column(Float, nullable=False)  # Available stock
    month_of_year = Column(Integer, nullable=False)  # Month of year (1-12)
    regional_demand = Column(Float, nullable=False)  # Regional demand
    restock_time = Column(Float, nullable=True)  # Restock time in days
    shortage = Column(Boolean, nullable=False)  # 1 if shortage occurred, 0 otherwise
    movement_id = Column(Integer, ForeignKey("movements.id"))
    movement = relationship("Movement", back_populates="predictions")

# Importar el modelo User, Role y UserStatus
from .user import User, Role, UserStatus