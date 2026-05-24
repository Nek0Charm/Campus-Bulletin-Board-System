from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class PostBase(BaseModel):
    title: str
    content: str
    board_id: UUID


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class AuthorInfo(BaseModel):
    id: UUID
    nickname: Optional[str]
    avatar_url: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PostRead(PostBase):
    id: UUID
    author_id: UUID
    author: AuthorInfo
    is_pinned: bool
    is_featured: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    items: List[PostRead]
    total: int
    page: int
    page_size: int
