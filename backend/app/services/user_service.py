from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import AdminUserData
from app.schemas.user import UserProfileData
from app.schemas.user import UserPublicData
from app.schemas.user import UpdateProfileRequest
from app.schemas.user import UpdateUserStatusRequest


class UserService:
    def get_profile(self, user: User) -> UserProfileData:
        return UserProfileData(
            id=str(user.id),
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            role=user.role,
            status=user.status,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )

    def update_profile(
        self, db: Session, user: User, payload: UpdateProfileRequest
    ) -> UserProfileData:
        if payload.nickname is not None:
            user.nickname = payload.nickname
        if payload.avatar_url is not None:
            user.avatar_url = payload.avatar_url
        db.add(user)
        db.commit()
        db.refresh(user)
        return self.get_profile(user)

    def get_public_profile(self, db: Session, user_id: str) -> UserPublicData:
        user = (
            db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserPublicData(
            id=str(user.id),
            username=user.username,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            role=user.role,
        )

    def list_users(
        self, db: Session, page: int = 1, page_size: int = 20
    ) -> tuple[list[AdminUserData], int]:
        query = db.query(User).filter(User.deleted_at.is_(None))
        total = query.count()
        users = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [
            AdminUserData(
                id=str(u.id),
                username=u.username,
                email=u.email,
                nickname=u.nickname,
                avatar_url=u.avatar_url,
                role=u.role,
                status=u.status,
                last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
                created_at=u.created_at.isoformat(),
            )
            for u in users
        ]
        return items, total

    def update_status(
        self, db: Session, user_id: str, payload: UpdateUserStatusRequest
    ) -> AdminUserData:
        user = (
            db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.status = payload.status
        db.add(user)
        db.commit()
        db.refresh(user)
        return AdminUserData(
            id=str(user.id),
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            role=user.role,
            status=user.status,
            last_login_at=(
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
            created_at=user.created_at.isoformat(),
        )
