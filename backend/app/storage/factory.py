from functools import lru_cache

from app.config import Settings
from app.config import get_settings
from app.storage.s3 import S3StorageBackend


@lru_cache
def get_storage_backend(settings: Settings | None = None) -> S3StorageBackend:
    settings = settings or get_settings()
    return S3StorageBackend(
        endpoint_url=settings.S3_ENDPOINT_URL,
        access_key_id=settings.S3_ACCESS_KEY_ID,
        secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
        region=settings.S3_REGION,
    )
