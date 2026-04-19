from typing import Generic
from typing import Optional
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    request_id: Optional[str] = None


class PaginationInfo(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class PaginatedData(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    pagination: PaginationInfo


class PaginatedResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: PaginatedData[T]
    request_id: Optional[str] = None


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    code: int
    message: str
    errors: Optional[list[ErrorDetail]] = None
    request_id: Optional[str] = None
