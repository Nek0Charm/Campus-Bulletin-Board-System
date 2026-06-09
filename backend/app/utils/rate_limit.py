import re
from dataclasses import dataclass
from typing import Awaitable
from typing import Callable

import redis
from fastapi import HTTPException
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.responses import Response

from app.config import get_settings
from app.deps.auth import decode_access_token
from app.utils.redis import get_redis

settings = get_settings()


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    methods: frozenset[str]
    path_pattern: re.Pattern[str]
    limit: int
    window_seconds: int
    scope: str

    def matches(self, method: str, path: str) -> bool:
        return method.upper() in self.methods and bool(self.path_pattern.match(path))


def _compile(path_pattern: str) -> re.Pattern[str]:
    return re.compile(path_pattern)


def build_rate_limit_rules() -> tuple[RateLimitRule, ...]:
    prefix = re.escape(settings.API_PREFIX.rstrip("/"))
    return (
        RateLimitRule(
            name="auth",
            methods=frozenset({"POST"}),
            path_pattern=_compile(rf"^{prefix}/auth/(login|register)/?$"),
            limit=settings.RATE_LIMIT_AUTH_LIMIT,
            window_seconds=settings.RATE_LIMIT_AUTH_WINDOW_SECONDS,
            scope="ip",
        ),
        RateLimitRule(
            name="content_write",
            methods=frozenset({"POST"}),
            path_pattern=_compile(rf"^{prefix}/(posts|comments)/?$"),
            limit=settings.RATE_LIMIT_CONTENT_LIMIT,
            window_seconds=settings.RATE_LIMIT_CONTENT_WINDOW_SECONDS,
            scope="user",
        ),
        RateLimitRule(
            name="likes",
            methods=frozenset({"POST", "DELETE"}),
            path_pattern=_compile(rf"^{prefix}/likes/(posts|comments)/[^/]+/?$"),
            limit=settings.RATE_LIMIT_LIKE_LIMIT,
            window_seconds=settings.RATE_LIMIT_LIKE_WINDOW_SECONDS,
            scope="user",
        ),
        RateLimitRule(
            name="public_read",
            methods=frozenset({"GET"}),
            path_pattern=_compile(rf"^{prefix}/(boards|posts|comments)(/.*)?$"),
            limit=settings.RATE_LIMIT_PUBLIC_LIMIT,
            window_seconds=settings.RATE_LIMIT_PUBLIC_WINDOW_SECONDS,
            scope="ip",
        ),
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rules = build_rate_limit_rules()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        rule = self._match_rule(request)
        if rule is None:
            return await call_next(request)

        identifier = self._identifier_for(request, rule)
        key = f"rate_limit:{rule.name}:{rule.scope}:{identifier}"

        try:
            limited, headers = self._consume(key, rule)
        except redis.RedisError:
            return await call_next(request)

        if limited:
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "message": "Too many requests",
                    "request_id": None,
                },
                headers=headers,
            )

        response = await call_next(request)
        response.headers.update(headers)
        return response

    def _match_rule(self, request: Request) -> RateLimitRule | None:
        method = request.method.upper()
        path = request.url.path
        for rule in self.rules:
            if rule.matches(method, path):
                return rule
        return None

    def _identifier_for(self, request: Request, rule: RateLimitRule) -> str:
        if rule.scope == "user":
            user_id = self._user_id_from_authorization(request)
            if user_id:
                return f"user:{user_id}"
        return f"ip:{self._client_ip(request)}"

    def _user_id_from_authorization(self, request: Request) -> str | None:
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        try:
            payload = decode_access_token(token)
        except HTTPException:
            return None
        subject = payload.get("sub")
        return str(subject) if subject else None

    def _client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
        return request.client.host if request.client else "unknown"

    def _consume(self, key: str, rule: RateLimitRule) -> tuple[bool, dict[str, str]]:
        client = get_redis()
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, rule.window_seconds)

        ttl = int(client.ttl(key))
        if ttl < 0:
            client.expire(key, rule.window_seconds)
            ttl = rule.window_seconds

        remaining = max(rule.limit - count, 0)
        headers = {
            "X-RateLimit-Limit": str(rule.limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(ttl),
        }
        return count > rule.limit, headers
