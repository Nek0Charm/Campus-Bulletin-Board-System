import hashlib
import logging

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
    return _redis


def _token_key(token: str) -> str:
    return f"token_blacklist:{hashlib.sha256(token.encode()).hexdigest()}"


def blacklist_token(token: str, ttl: int) -> None:
    try:
        r = get_redis()
        r.setex(_token_key(token), ttl, "1")
    except redis.RedisError:
        logger.warning("Redis unavailable, skipping token blacklist")


def is_token_blacklisted(token: str) -> bool:
    try:
        r = get_redis()
        return r.exists(_token_key(token)) > 0
    except redis.RedisError:
        logger.warning("Redis unavailable, skipping blacklist check")
        return False
