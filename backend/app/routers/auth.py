from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.deps import get_auth_service
from app.schemas import LoginData
from app.schemas import LoginRequest
from app.schemas import LogoutData
from app.schemas import RegisterData
from app.schemas import RegisterRequest
from app.schemas.response import ApiResponse
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[RegisterData])
async def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
):
    return ApiResponse[RegisterData](data=service.register(db, payload))


@router.post("/login", response_model=ApiResponse[LoginData])
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
):
    return ApiResponse[LoginData](data=service.login(db, payload))


@router.post("/logout", response_model=ApiResponse[LogoutData])
async def logout(service: AuthService = Depends(get_auth_service)):
    return ApiResponse[LogoutData](data=service.logout())
