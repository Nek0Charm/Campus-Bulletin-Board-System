from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.models.moderation_log import ModerationAction
from app.models.report import ReportStatus
from app.models.report import ReportTargetType


class ReportCreate(BaseModel):
    target_type: ReportTargetType
    target_id: UUID
    reason: str = Field(..., min_length=1, max_length=255)


class ReportRead(BaseModel):
    id: UUID
    reporter_id: UUID
    target_type: str
    target_id: UUID
    reason: str
    status: str
    handled_by: UUID | None = None
    handled_at: datetime | None = None
    result_note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportResolveRequest(BaseModel):
    status: ReportStatus = Field(
        ..., description="Only resolved or dismissed is allowed."
    )
    result_note: str | None = Field(default=None, max_length=2000)


class ModerationLogRead(BaseModel):
    id: UUID
    report_id: UUID
    operator_id: UUID
    action: ModerationAction | str
    target_type: str
    target_id: UUID
    detail: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
