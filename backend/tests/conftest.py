import sys
from pathlib import Path

# 确保 backend/ 在 sys.path 中，使 `from app.xxx` 在测试里可用
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fakeredis
import pytest

_fake_redis = fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture(autouse=True)
def _override_redis():
    """每个测试使用 fakeredis 替代真实 Redis。"""
    import app.utils.redis as redis_mod

    original = redis_mod._redis
    redis_mod._redis = _fake_redis
    yield
    redis_mod._redis = original
    _fake_redis.flushall()
