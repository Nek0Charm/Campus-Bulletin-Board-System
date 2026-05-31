from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=5000)
    is_published: bool = Field(default=False)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    is_published: bool | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @field_validator("title", "content", mode="before")
    @classmethod
    def reject_none(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v


class AnnouncementRead(BaseModel):
    id: UUID
    title: str
    content: str
    is_published: bool
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
