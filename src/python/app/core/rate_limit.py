import math
import time

from src.python.app.core.redis import get_redis_client
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_limit: int = 120, redis_enabled: bool = False) -> None:
        super().__init__(app)
        self.default_limit = default_limit
        self.redis_enabled = redis_enabled
        self.window_seconds = 60
        self.custom_limits = {
            "/api/v1/auth/login": 5,
            "/api/v1/auth/register": 3,
            "/api/v1/checkout/create-session": 5,
        }
        # In-memory fallback used when Redis is unavailable (single-process only).
        # Maps key -> (count, window_expiry_monotonic).
        self._memory_store: dict[str, tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/docs", "/redoc", "/openapi.json"}:
            return await call_next(request)

        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")

        key = f"rate_limit:{client_ip}:{request.url.path}"
        limit_for_path = self.custom_limits.get(request.url.path, self.default_limit)

        if self.redis_enabled:
            try:
                redis_client = await get_redis_client()
                allowed, retry_after = await self._check_redis(redis_client, key, limit_for_path)
            except Exception:
                # Redis unreachable — fall back to in-memory counting.
                allowed, retry_after = self._check_memory(key, limit_for_path)
        else:
            allowed, retry_after = self._check_memory(key, limit_for_path)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry later."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)

    async def _check_redis(self, redis_client, key: str, limit: int) -> tuple[bool, int]:
        current = await redis_client.get(key)
        current_count = int(current) if current else 0

        if current_count >= limit:
            ttl = await redis_client.ttl(key)
            return False, ttl if ttl and ttl > 0 else self.window_seconds

        await redis_client.incr(key)
        if current_count == 0:
            await redis_client.expire(key, self.window_seconds)

        return True, 0

    def _check_memory(self, key: str, limit: int) -> tuple[bool, int]:
        now = time.monotonic()

        # Opportunistically drop expired entries to bound memory growth.
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
