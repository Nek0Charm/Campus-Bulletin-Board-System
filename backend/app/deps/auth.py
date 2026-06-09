from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps.db import get_db
from app.models import User
from app.utils.redis import is_token_blacklisted

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")
_optional_bearer = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, role: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": user_id, "role": role, "exp": expire_at}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, object]:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    payload = decode_access_token(token)
    try:
        user_id = UUID(str(payload.get("sub")))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token subject") from exc

    # 查询时筛选deleted_at为None，忽略软删除的数据
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user.status != "active":
        raise HTTPException(status_code=403, detail=f"User is {user.status}")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        token = credentials.credentials
        if is_token_blacklisted(token):
            return None
        payload = decode_access_token(token)
        user_id = UUID(str(payload.get("sub")))
        user = (
            db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        )
        if not user or user.status != "active" or not user.email_verified:
            return None
        return user
    except Exception:
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user


def check_not_muted(current_user: User) -> None:
    """Raise 403 if user is currently muted."""
    if current_user.muted_until is None:
        return
    expired = current_user.muted_until
    if expired.tzinfo is None:
        expired = expired.replace(tzinfo=timezone.utc)
    if expired > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=403,
            detail=f"You are muted until {expired.isoformat()}",
        )


def check_can_moderate_post(db: Session, current_user: User, post: object) -> None:
    """Raise 403 if user cannot moderate this post.
    Admins can always moderate. Board masters can moderate posts in their boards."""
    if current_user.role == "admin":
        return
    # Lazy import to avoid circular dependency
    from app.services.board_master_service import BoardMasterService

    bm_service = BoardMasterService()
    if bm_service.is_board_master(db, board_id=post.board_id, user_id=current_user.id):
        return
    raise HTTPException(status_code=403, detail="Admin or board master required")


def check_can_moderate_board(db: Session, current_user: User, board_id: UUID) -> None:
    """Raise 403 if user cannot moderate this board.
    Admins can always moderate. Board masters of this specific board can moderate."""
    if current_user.role == "admin":
        return
    # Lazy import to avoid circular dependency
    from app.services.board_master_service import BoardMasterService

    bm_service = BoardMasterService()
    if bm_service.is_board_master(db, board_id=board_id, user_id=current_user.id):
        return
    raise HTTPException(status_code=403, detail="Admin or board master required")
