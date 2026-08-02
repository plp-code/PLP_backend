import math
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.python.app.core.redis import get_redis_client


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
            "/api/v1/checkout/create-session": 5,
            
        }
        self._memory_store: dict[str, tuple[int, float]] = {}

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

        key = f"rate_limit:{client_ip}:{path}"
        limit_for_path = self.custom_limits.get(path, self.default_limit)

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