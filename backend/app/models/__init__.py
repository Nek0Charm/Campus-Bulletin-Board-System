"""
models 层定义 ORM 实体，映射数据库表结构与约束。

被 services 层用于查询与持久化。


"""

from app.models.base import Base
from app.models.base import IDMixin
from app.models.base import TimestampMixin
from app.models.user import User
from app.models.post import Post
from app.models.board import Board
from app.models.comment import Comment
from app.models.notification import Notification
from app.models.like import PostLike, CommentLike
from app.models.media import MediaAsset, PostAttachment
from app.models.announcement import Announcement

__all__ = [
    "Base",
    "IDMixin",
    "TimestampMixin",
    "User",
    "Post",
    "Board",
    "Comment",
    "Notification",
    "PostLike",
    "CommentLike",
    "MediaAsset",
    "PostAttachment",
    "Announcement",
]
