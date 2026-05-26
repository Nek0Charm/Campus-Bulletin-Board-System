from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class NotificationRead(BaseModel):
    id: UUID
    type: str
    title: str
    content: str
    related_type: str | None = None
    related_id: UUID | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUnreadCount(BaseModel):
    unread_count: int


class NotificationMarkAllReadResult(BaseModel):
    updated_count: int
    unread_count: int
