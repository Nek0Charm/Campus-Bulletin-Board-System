from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0)


class BoardRead(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    sort_order: int
    post_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    slug: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    sort_order: int | None = None

    @field_validator("name", "slug", mode="before")
    @classmethod
    def reject_none(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v
