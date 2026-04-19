from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User
from app.schemas.auth import AuthUserData
from app.schemas.auth import LoginData
from app.schemas.auth import LoginRequest
from app.schemas.auth import LogoutData
from app.schemas.auth import RegisterData
from app.schemas.auth import RegisterRequest
from app.utils.security import hash_password
from app.utils.security import verify_password

settings = get_settings()


def _create_access_token(user_id: str, role: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": user_id, "role": role, "exp": expire_at}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


class AuthService:
    def register(self, db: Session, payload: RegisterRequest) -> RegisterData:
        existing = (
            db.query(User)
            .filter(or_(User.username == payload.username, User.email == payload.email))
            .first()
        )
        if existing and existing.username == payload.username:
            raise HTTPException(status_code=409, detail="Username already exists")
        if existing and existing.email == payload.email:
            raise HTTPException(status_code=409, detail="Email already exists")

        user = User(
            username=payload.username,
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            nickname=payload.nickname or None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return RegisterData(
            user=AuthUserData(
                id=str(user.id),
                username=user.username,
                email=user.email,
                nickname=user.nickname,
                role=user.role,
                status=user.status,
            )
        )

    def login(self, db: Session, payload: LoginRequest) -> LoginData:
        user = (
            db.query(User)
            .filter(
                or_(User.username == payload.account, User.email == payload.account)
            )
            .first()
        )
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid account or password")
        if user.status != "active":
            raise HTTPException(status_code=403, detail=f"User is {user.status}")

        user.last_login_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)

        access_token = _create_access_token(str(user.id), user.role)
        return LoginData(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=AuthUserData(
                id=str(user.id),
                username=user.username,
                email=user.email,
                nickname=user.nickname,
                role=user.role,
                status=user.status,
            ),
        )

    def logout(self) -> LogoutData:
        return LogoutData(message="logout success")
