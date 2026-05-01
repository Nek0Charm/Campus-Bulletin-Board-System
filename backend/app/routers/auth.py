from fastapi import APIRouter
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps import get_auth_service
from app.deps import get_current_user
from app.deps import get_db
from app.models import User
from app.schemas import LoginData
from app.schemas import LoginRequest
from app.schemas import LogoutData
from app.schemas import RegisterData
from app.schemas import RegisterRequest
from app.schemas import ResetPasswordData
from app.schemas import ResetPasswordRequest
from app.schemas.response import ApiResponse
from app.services import AuthService

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


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
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return ApiResponse[LogoutData](data=service.logout(token))


@router.post("/reset-password", response_model=ApiResponse[ResetPasswordData])
async def reset_password(
    payload: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
):
    return ApiResponse[ResetPasswordData](
        data=service.reset_password(db, current_user, payload)
    )
