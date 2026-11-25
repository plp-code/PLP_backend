import math
import re
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.python.app.core.redis import get_redis_client
from src.python.app.core.config import settings


# Keyed limits for things the per-IP middleware can't see (an email or a
# session_id in the request body). Same backend rules as the middleware:
# Redis when enabled, otherwise per-process memory.
_key_store: dict[str, tuple[int, float]] = {}


def _hit_memory(key: str, limit: int, window_seconds: int) -> bool:
    now = time.monotonic()
    if len(_key_store) > 10_000:
        for k in [k for k, (_, exp) in _key_store.items() if exp <= now]:
            del _key_store[k]
    count, expiry = _key_store.get(key, (0, 0.0))
    if now >= expiry:
        count, expiry = 0, now + window_seconds
    if count >= limit:
        return False
    _key_store[key] = (count + 1, expiry)
    return True


async def hit_key_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Count one hit against `key`. Returns True if still within the limit."""
    full_key = f"rate_limit:key:{key}"
    if settings.REDIS_ENABLED:
        try:
            redis_client = await get_redis_client()
            pipe = redis_client.pipeline()
            pipe.incr(full_key)
            pipe.ttl(full_key)
            count, ttl = await pipe.execute()
            if count == 1 or ttl == -1:
                await redis_client.expire(full_key, window_seconds)
            return count <= limit
        except Exception:
            pass
    return _hit_memory(full_key, limit, window_seconds)


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_limit: int = 120, redis_enabled: bool = False) -> None:
        super().__init__(app)
        self.default_limit = default_limit
        self.redis_enabled = redis_enabled
        self.window_seconds = 60
        self.custom_limits = {
            "/api/v1/auth/login": 5,
            "/api/v1/auth/register": 3,
            "/api/v1/auth/forgot-password": 3,
            "/api/v1/auth/magic-link": 3,
            "/api/v1/checkout/create-session": 5,
            "/api/v1/checkout/resend-claim": 3,

        }
        self.pattern_limits: list[tuple[re.Pattern, str, int]] = [
            (
                re.compile(r"^/api/v1/maps/[^/]+/join-waitlist$"),
                "/api/v1/maps/{slug}/join-waitlist",
                5,
            ),
        ]
        self._memory_store: dict[str, tuple[int, float]] = {}
        
    def _resolve_limit(self, path: str) -> tuple[str, int]:
        """Return (bucket, limit). The bucket replaces the raw path in the counter key."""
        if path in self.custom_limits:
            return path, self.custom_limits[path]
        for pattern, bucket, limit in self.pattern_limits:
            if pattern.match(path):
                return bucket, limit
        return path, self.default_limit

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"

        if path in {"/docs", "/redoc", "/openapi.json"}:
            return await call_next(request)

        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else (request.client.host if request.client else "unknown")
        )

        bucket, limit_for_path = self._resolve_limit(path)
        key = f"rate_limit:{client_ip}:{bucket}"

        if self.redis_enabled:
            try:
                redis_client = await get_redis_client()
                allowed, retry_after = await self._check_redis(redis_client, key, limit_for_path)
            except Exception:
    
                allowed, retry_after = self._check_memory(key, limit_for_path)
        else:
            allowed, retry_after = self._check_memory(key, limit_for_path)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)

    async def _check_redis(self, redis_client, key: str, limit: int) -> tuple[bool, int]:
        """
        Atomic Redis Increment using a Pipeline.
        Prevents race conditions when requests land at the exact same millisecond.
        """
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        results = await pipe.execute()
        
        current_count = results[0]
        ttl = results[1]
        
        if ttl == -1:
            await redis_client.expire(key, self.window_seconds)
            ttl = self.window_seconds

        if current_count == 1:
            await redis_client.expire(key, self.window_seconds)
            ttl = self.window_seconds

        if current_count > limit:
            retry_after = ttl if ttl and ttl > 0 else self.window_seconds
            return False, retry_after

        return True, 0

    def _check_memory(self, key: str, limit: int) -> tuple[bool, int]:
        now = time.monotonic()

        if len(self._memory_store) > 10_000:
            self._memory_store = {
                k: (c, exp) for k, (c, exp) in self._memory_store.items() if exp > now
            }

        count, expiry = self._memory_store.get(key, (0, 0.0))
        if now >= expiry:
            count, expiry = 0, now + self.window_seconds

        if count >= limit:
            return False, max(1, math.ceil(expiry - now))

        self._memory_store[key] = (count + 1, expiry)
        return True, 0