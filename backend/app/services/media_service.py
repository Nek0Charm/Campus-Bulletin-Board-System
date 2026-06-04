import hashlib
import logging
import os
import uuid
from datetime import datetime
from datetime import timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from app.config import get_settings
from app.models.media import MediaAsset
from app.models.media import PostAttachment
from app.storage.base import StorageBackend

logger = logging.getLogger(__name__)


def _get_settings():
    return get_settings()


def _allowed_mime_types():
    s = _get_settings()
    return set(s.UPLOAD_ALLOWED_MIME_TYPES.split(","))


def _max_file_size():
    s = _get_settings()
    return s.UPLOAD_MAX_SIZE_MB * 1024 * 1024


class MediaService:
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    def upload(
        self,
        db: Session,
        *,
        file_data: bytes,
        file_name: str,
        mime_type: str,
        file_size: int,
        uploader_id: UUID,
        source_type: str,
        source_id: UUID | None = None,
        is_public: bool = True,
    ) -> MediaAsset:
        s = _get_settings()
        if mime_type not in _allowed_mime_types():
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {mime_type}",
            )
        if file_size > _max_file_size():
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {s.UPLOAD_MAX_SIZE_MB}MB",
            )

        sha256 = hashlib.sha256(file_data).hexdigest()

        existing = (
            db.query(MediaAsset)
            .filter(
                MediaAsset.sha256 == sha256,
                MediaAsset.uploader_id == uploader_id,
                MediaAsset.deleted_at.is_(None),
            )
            .first()
        )
        if existing:
            return existing

        ext = os.path.splitext(file_name)[1] or ".bin"
        object_key = f"{source_type}/{uploader_id}/{uuid.uuid4().hex}{ext}"

        self.storage.put(object_key, file_data, mime_type)

        db_obj = MediaAsset(
            uploader_id=uploader_id,
            bucket=s.S3_BUCKET_NAME,
            object_key=object_key,
            url="",
            file_name=file_name,
            mime_type=mime_type,
            file_size=file_size,
            sha256=sha256,
            source_type=source_type,
            source_id=source_id,
            is_public=is_public,
        )
        db.add(db_obj)
        db.flush()
        db_obj.url = f"/api/v1/media/{db_obj.id}"
        try:
            db.commit()
        except Exception:
            db.rollback()
            try:
                self.storage.delete(object_key)
            except Exception:
                logger.exception(
                    "Failed to cleanup S3 object %s after DB error", object_key
                )
            raise
        db.refresh(db_obj)
        return db_obj

    def get_by_id(self, db: Session, id: UUID) -> MediaAsset | None:
        return (
            db.query(MediaAsset)
            .filter(MediaAsset.id == id, MediaAsset.deleted_at.is_(None))
            .first()
        )

    def get_file(self, db: Session, id: UUID) -> tuple[bytes, str]:
        asset = self.get_by_id(db, id)
        if not asset:
            raise HTTPException(status_code=404, detail="Media not found")

        data = self.storage.get(asset.object_key)
        return data, asset.mime_type

    def delete(
        self, db: Session, id: UUID, user_id: UUID, is_admin: bool = False
    ) -> None:
        asset = self.get_by_id(db, id)
        if not asset:
            raise HTTPException(status_code=404, detail="Media not found")
        if not is_admin and asset.uploader_id != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        asset.deleted_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        try:
            self.storage.delete(asset.object_key)
        except Exception:
            logger.exception(
                "Failed to delete S3 object %s; DB row already soft-deleted",
                asset.object_key,
            )

    def list_by_post(self, db: Session, post_id: UUID) -> list[MediaAsset]:
        attachments = (
            db.query(PostAttachment)
            .filter(PostAttachment.post_id == post_id)
            .order_by(PostAttachment.sort_order)
            .all()
        )
        media_ids = [a.media_id for a in attachments]
        if not media_ids:
            return []
        return (
            db.query(MediaAsset)
            .filter(
                MediaAsset.id.in_(media_ids),
                MediaAsset.deleted_at.is_(None),
            )
            .all()
        )

    def attach_to_post(
        self,
        db: Session,
        post_id: UUID,
        media_ids: list[UUID],
    ) -> list[PostAttachment]:
        existing = (
            db.query(sa_func.count(PostAttachment.id))
            .filter(PostAttachment.post_id == post_id)
            .scalar()
        )
        s = _get_settings()
        if existing + len(media_ids) > s.UPLOAD_MAX_PER_POST:
            raise HTTPException(
                status_code=400,
                detail=f"Exceeded maximum of {s.UPLOAD_MAX_PER_POST} attachments per post",
            )

        for mid in media_ids:
            asset = self.get_by_id(db, mid)
            if not asset:
                raise HTTPException(status_code=404, detail=f"Media {mid} not found")

        attachments = []
        for idx, mid in enumerate(media_ids):
            att = PostAttachment(
                post_id=post_id,
                media_id=mid,
                sort_order=existing + idx,
            )
            db.add(att)
            attachments.append(att)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        for a in attachments:
            db.refresh(a)
        return attachments

    def update_avatar(
        self,
        db: Session,
        file_data: bytes,
        file_name: str,
        mime_type: str,
        file_size: int,
        user_id: UUID,
    ) -> str:
        from app.models.user import User

        asset = self.upload(
            db,
            file_data=file_data,
            file_name=file_name,
            mime_type=mime_type,
            file_size=file_size,
            uploader_id=user_id,
            source_type="avatar",
            source_id=user_id,
        )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_avatar_url = user.avatar_url
        user.avatar_url = f"/api/v1/media/{asset.id}"
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(user)

        if old_avatar_url:
            old_id = old_avatar_url.rsplit("/", 1)[-1]
            try:
                old_uuid = UUID(old_id)
            except ValueError:
                old_uuid = None
            if old_uuid and old_uuid != asset.id:
                old_asset = self.get_by_id(db, old_uuid)
                if old_asset and old_asset.source_type == "avatar":
                    old_asset.deleted_at = datetime.now(timezone.utc)
                    try:
                        db.commit()
                    except Exception:
                        db.rollback()
                    try:
                        self.storage.delete(old_asset.object_key)
                    except Exception:
                        logger.exception(
                            "Failed to delete old avatar S3 object %s",
                            old_asset.object_key,
                        )

        return user.avatar_url
