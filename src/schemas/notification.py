from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from src.models.notification import NotificationType, NotificationLevel


class NotificationBase(BaseModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    level: NotificationLevel = NotificationLevel.LOW
    read: bool = False
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    metadata_: Optional[dict] = None
    user_id: int

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    level: NotificationLevel = NotificationLevel.LOW
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    metadata_: Optional[dict] = None
    user_id: int

class NotificationUpdate(BaseModel):
    read: Optional[bool] = None
    resolved_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    count: int
