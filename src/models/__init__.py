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

# Import new models
from .notification import (
    Notification, NotificationCreate, NotificationUpdate, NotificationInDB,
    NotificationType, NotificationLevel
)
from .order import (
    Order, OrderCreate, OrderUpdate, OrderInDB, OrderStatus
)
from .report import (
    Report, ReportCreate, ReportUpdate, ReportInDB,
    ReportType, ReportFormat, ReportStatus
)
from .forecast import (
    ForecastRun, ForecastRunCreate, ForecastRunResponse,
    ForecastPoint, ForecastPointResponse, ForecastFullResponse
)
from .supplier import (
    Supplier, SupplierCreate, SupplierUpdate, SupplierInDB, SupplierStatus
)
from .lot import (
    Lot, LotCreate, LotUpdate, LotInDB, LotStatus,
    LotEvent, LotEventCreate, LotEventInDB
)
from .audit import (
    Audit, AuditCreate, AuditUpdate, AuditInDB, AuditStatus
)
from .delivery import (
    Delivery, DeliveryCreate, DeliveryUpdate, DeliveryInDB, DeliveryStatus
)

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
    'MedicationConditionLink',

    # Notifications
    'Notification', 'NotificationCreate', 'NotificationUpdate', 'NotificationInDB',
    'NotificationType', 'NotificationLevel',

    # Orders
    'Order', 'OrderCreate', 'OrderUpdate', 'OrderInDB', 'OrderStatus',

    # Reports
    'Report', 'ReportCreate', 'ReportUpdate', 'ReportInDB',
    'ReportType', 'ReportFormat', 'ReportStatus',

    # Forecasts
    'ForecastRun', 'ForecastRunCreate', 'ForecastRunResponse',
    'ForecastPoint', 'ForecastPointResponse', 'ForecastFullResponse',

    # Logistics: Suppliers, Lots/Traceability, Audits, Deliveries
    'Supplier', 'SupplierCreate', 'SupplierUpdate', 'SupplierInDB', 'SupplierStatus',
    'Lot', 'LotCreate', 'LotUpdate', 'LotInDB', 'LotStatus',
    'LotEvent', 'LotEventCreate', 'LotEventInDB',
    'Audit', 'AuditCreate', 'AuditUpdate', 'AuditInDB', 'AuditStatus',
    'Delivery', 'DeliveryCreate', 'DeliveryUpdate', 'DeliveryInDB', 'DeliveryStatus',
]