import sys
from pathlib import Path

import fakeredis
import pytest

# 确保 backend/ 在 sys.path 中，使 `from app.xxx` 在测试里可用
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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


@pytest.fixture(autouse=True)
def _disable_rate_limit_for_non_rate_limit_tests(request, monkeypatch):
    """Keep cross-cutting rate limits from affecting unrelated API tests."""
    if Path(str(request.path)).name == "test_rate_limit.py":
        yield
        return

    import app.utils.rate_limit as rate_limit_mod

    monkeypatch.setattr(rate_limit_mod.settings, "RATE_LIMIT_ENABLED", False)
    yield
