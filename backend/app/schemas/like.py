from uuid import UUID

from pydantic import BaseModel


class PostLikeStatus(BaseModel):
    is_liked: bool
    liked_comment_ids: list[UUID]
