from pydantic import BaseModel, ConfigDict, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=50000)
    board_id: UUID


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1, max_length=50000)

    @field_validator("title", "content", mode="before")
    @classmethod
    def reject_none(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v


class AuthorInfo(BaseModel):
    id: UUID
    username: str
    nickname: Optional[str]
    avatar_url: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PostRead(PostBase):
    id: UUID
    author_id: UUID
    author: AuthorInfo
    is_pinned: bool
    is_featured: bool
    status: str = "normal"
    published_at: Optional[datetime] = None
    like_count: int = 0
    comment_count: int = 0
    is_liked: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    items: List[PostRead]
    total: int
    page: int
    page_size: int
