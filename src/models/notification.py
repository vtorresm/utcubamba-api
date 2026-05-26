from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from .user import User

class NotificationType(str, Enum):
    SHORTAGE_ALERT = "shortage_alert"
    STOCK_ALERT = "stock_alert"
    ORDER_UPDATE = "order_update"
    SYSTEM = "system"
    INFO = "info"

class NotificationLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class NotificationBase(SQLModel):
    title: str = Field(..., max_length=200, nullable=False)
    message: str = Field(..., max_length=2000, nullable=False)
    type: NotificationType = Field(default=NotificationType.INFO, nullable=False)
    level: NotificationLevel = Field(default=NotificationLevel.LOW, nullable=False)
    read: bool = Field(default=False, nullable=False)
    related_entity_type: Optional[str] = Field(default=None, max_length=50)
    related_entity_id: Optional[int] = Field(default=None)
    resolved_at: Optional[datetime] = Field(default=None)
    metadata_: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    user_id: int = Field(foreign_key="users.id", nullable=False)

class Notification(NotificationBase, table=True):
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: "User" = Relationship(back_populates="notifications")

class NotificationCreate(SQLModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    level: NotificationLevel = NotificationLevel.LOW
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    metadata_: Optional[dict] = None
    user_id: int

class NotificationUpdate(SQLModel):
    read: Optional[bool] = None
    resolved_at: Optional[datetime] = None

class NotificationInDB(NotificationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
