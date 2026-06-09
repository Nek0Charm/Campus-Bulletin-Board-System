from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict


class NotificationActor(BaseModel):
    id: UUID
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationRead(BaseModel):
    id: UUID
    actor: Optional[NotificationActor] = None
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
