from datetime import datetime
from datetime import timezone

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps.auth import create_access_token, decode_access_token
from app.models.user import User
from app.schemas.auth import AuthUserData
from app.schemas.auth import LoginData
from app.schemas.auth import LoginRequest
from app.schemas.auth import LogoutData
from app.schemas.auth import RegisterData
from app.schemas.auth import RegisterRequest
from app.schemas.auth import ResetPasswordData
from app.schemas.auth import ResetPasswordRequest
from app.services.email_service import EmailService
from app.utils.redis import blacklist_token
from app.utils.security import hash_password
from app.utils.security import verify_password

settings = get_settings()


class AuthService:
    def register(
        self, db: Session, payload: RegisterRequest, email_service: EmailService
    ) -> RegisterData:
        existing = (
            db.query(User)
            .filter(
                or_(User.username == payload.username, User.email == payload.email),
                User.deleted_at.is_(None),
            )
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

        # 使用 try-except 确保数据库操作的原子性
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409, detail="Username or email already exists"
            )
        except Exception:
            db.rollback()
            raise
        db.refresh(user)

        try:
            verify_token = email_service.generate_verify_token(str(user.id), user.email)
            email_service.send_verification_email(user.email, verify_token)
        except Exception:
            db.rollback()
            raise

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
                or_(User.username == payload.account, User.email == payload.account),
                User.deleted_at.is_(None),
            )
            .first()
        )
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid account or password")
        if user.status != "active":
            raise HTTPException(status_code=403, detail=f"User is {user.status}")
        if not user.email_verified:
            raise HTTPException(status_code=403, detail="Email not verified")

        user.last_login_at = datetime.now(timezone.utc)
        db.add(user)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(user)

        access_token = create_access_token(str(user.id), user.role)
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

    def logout(self, token: str) -> LogoutData:
        payload = decode_access_token(token)
        exp = int(payload.get("exp", 0))
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = max(exp - now, 0)
        if ttl > 0:
            blacklist_token(token, ttl)
        return LogoutData(message="logout success")

    def reset_password(
        self, db: Session, user: User, payload: ResetPasswordRequest, token: str
    ) -> ResetPasswordData:
        if not verify_password(payload.old_password, user.password_hash):
            raise HTTPException(status_code=401, detail="Old password is incorrect")
        user.password_hash = hash_password(payload.new_password)
        db.add(user)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        decoded = decode_access_token(token)
        exp = int(decoded.get("exp", 0))
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = max(exp - now, 0)
        if ttl > 0:
            blacklist_token(token, ttl)

        return ResetPasswordData(message="password reset success")
