import logging
from functools import lru_cache

from app.config import Settings
from app.config import get_settings
from app.storage.base import StorageBackend
from app.storage.memory import InMemoryStorageBackend
from app.storage.s3 import S3StorageBackend

logger = logging.getLogger(__name__)


@lru_cache
def get_storage_backend(settings: Settings | None = None) -> StorageBackend:
    settings = settings or get_settings()
    if not settings.S3_ACCESS_KEY_ID or not settings.S3_SECRET_ACCESS_KEY:
        logger.warning("S3 credentials not configured — using in-memory storage (dev only)")
        return InMemoryStorageBackend()
    return S3StorageBackend(
        endpoint_url=settings.S3_ENDPOINT_URL,
        access_key_id=settings.S3_ACCESS_KEY_ID,
        secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
        region=settings.S3_REGION,
    )
