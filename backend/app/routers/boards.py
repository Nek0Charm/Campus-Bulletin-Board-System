from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.deps.auth import require_admin
from app.deps.db import get_db
from app.deps.services import get_board_service
from app.models.user import User
from app.schemas.board import BoardCreate
from app.schemas.board import BoardRead
from app.schemas.board import BoardUpdate
from app.schemas.response import ApiResponse
from app.services.board_service import BoardService

router = APIRouter(prefix="/boards", tags=["boards"])


@router.post(
    "",
    response_model=ApiResponse[BoardRead],
    status_code=status.HTTP_201_CREATED,
)
def create_board(
    payload: BoardCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
    service: BoardService = Depends(get_board_service),
):
    if service.slug_exists(db, payload.slug):
        raise HTTPException(status_code=409, detail="Board slug already exists")
    if service.name_exists(db, payload.name):
        raise HTTPException(status_code=409, detail="Board name already exists")
    return ApiResponse(data=service.create(db, obj_in=payload))


@router.get("", response_model=ApiResponse[list[BoardRead]])
def list_boards(
    db: Session = Depends(get_db),
    service: BoardService = Depends(get_board_service),
):
    return ApiResponse(data=service.get_all(db))


@router.get("/{id}", response_model=ApiResponse[BoardRead])
def get_board(
    id: UUID,
    db: Session = Depends(get_db),
    service: BoardService = Depends(get_board_service),
):
    board = service.get_by_id(db, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return ApiResponse(data=board)


@router.patch("/{id}", response_model=ApiResponse[BoardRead])
def update_board(
    id: UUID,
    payload: BoardUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
    service: BoardService = Depends(get_board_service),
):
    board = service.get_by_id(db, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if payload.slug and service.slug_exists(db, payload.slug, exclude_id=id):
        raise HTTPException(status_code=409, detail="Board slug already exists")
    if payload.name and service.name_exists(db, payload.name, exclude_id=id):
        raise HTTPException(status_code=409, detail="Board name already exists")
    return ApiResponse(data=service.update(db, db_obj=board, obj_in=payload))


@router.delete("/{id}", response_model=ApiResponse)
def delete_board(
    id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
    service: BoardService = Depends(get_board_service),
):
    board = service.get_by_id(db, id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    service.remove(db, db_obj=board)
    return ApiResponse(message="Board deleted")
