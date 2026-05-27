from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.post import AuthorInfo


class CommentCreate(BaseModel):
    post_id: UUID
    content: str
    parent_comment_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    content: str


class CommentRead(BaseModel):
    id: UUID
    post_id: UUID
    author_id: UUID
    author: AuthorInfo
    content: str
    parent_comment_id: Optional[UUID] = None
    root_comment_id: Optional[UUID] = None
    like_count: int
    reply_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentWithReplies(CommentRead):
    replies: List[CommentRead] = []
