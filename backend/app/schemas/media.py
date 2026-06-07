from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class MediaUploadResponse(BaseModel):
    id: UUID
    url: str
    file_name: str
    mime_type: str
    file_size: int
    width: int | None = None
    height: int | None = None


class MediaRead(BaseModel):
    id: UUID
    uploader_id: UUID
    url: str
    file_name: str
    mime_type: str
    file_size: int
    width: int | None = None
    height: int | None = None
    source_type: str
    source_id: UUID | None = None
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostAttachmentCreate(BaseModel):
    media_ids: list[UUID] = Field(..., max_length=20)


class PostAttachmentRead(BaseModel):
    id: UUID
    post_id: UUID
    media_id: UUID
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AvatarUploadResponse(BaseModel):
    avatar_url: str
