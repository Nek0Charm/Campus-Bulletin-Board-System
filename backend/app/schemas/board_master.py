from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BoardMasterUserInfo(BaseModel):
    id: UUID
    username: str
    nickname: str | None = None
    avatar_url: str | None = None
    model_config = ConfigDict(from_attributes=True)


class BoardMasterRead(BaseModel):
    id: UUID
    board_id: UUID
    user_id: UUID
    user: BoardMasterUserInfo
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AddBoardMasterRequest(BaseModel):
    user_id: UUID
