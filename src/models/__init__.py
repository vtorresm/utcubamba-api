# src/models/__init__.py
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TypeVar, Generic, Type, Any
from datetime import datetime

# Import base models
from .base import Base, BaseModel, Role, UserStatus

# Import all models
from .user import User, UserCreate, UserUpdate, UserInDB
from .password_reset_token import (
    PasswordResetToken, 
    PasswordResetTokenCreate,
    PasswordResetTokenResponse,
    PasswordResetRequest
)

# Import domain models
from .category import Category, CategoryCreate, CategoryUpdate, CategoryInDB
from .condition import Condition, ConditionCreate, ConditionUpdate, ConditionInDB
from .intake_type import IntakeType, IntakeTypeCreate, IntakeTypeUpdate, IntakeTypeInDB
from .medication import Medication, MedicationCreate, MedicationUpdate, MedicationInDB
from .movement import Movement, MovementCreate, MovementUpdate, MovementInDB, MovementType
from .prediction import (
    Prediction, PredictionCreate, PredictionUpdate, PredictionInDB, PredictionResponse,
    PredictionMetrics, PredictionMetricsCreate, PredictionMetricsUpdate, PredictionMetricsResponse
)
from .medication_condition import MedicationConditionLink

# Re-export all models
__all__ = [
    # Base
    'Base', 'BaseModel', 'SQLModel', 'Role', 'UserStatus',
    
    # User & Auth
    'User', 'UserCreate', 'UserUpdate', 'UserInDB',
    'PasswordResetToken', 'PasswordResetTokenCreate',
    'PasswordResetTokenResponse', 'PasswordResetRequest',
    
    # Domain Models
    'Category', 'CategoryCreate', 'CategoryUpdate', 'CategoryInDB',
    'Condition', 'ConditionCreate', 'ConditionUpdate', 'ConditionInDB',
    'IntakeType', 'IntakeTypeCreate', 'IntakeTypeUpdate', 'IntakeTypeInDB',
    'Medication', 'MedicationCreate', 'MedicationUpdate', 'MedicationInDB',
    'Movement', 'MovementCreate', 'MovementUpdate', 'MovementInDB', 'MovementType',
    'Prediction', 'PredictionCreate', 'PredictionUpdate', 'PredictionInDB', 'PredictionResponse',
    'PredictionMetrics', 'PredictionMetricsCreate', 'PredictionMetricsUpdate', 'PredictionMetricsResponse',
    'MedicationConditionLink'
]