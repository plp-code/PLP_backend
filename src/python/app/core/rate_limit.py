from src.python.app.core.redis import get_redis_client
from fastapi import Request 
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_limit: int = 120) -> None:
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = 60
        self.custom_limits = {
            "/api/v1/auth/login": 5,
            "/api/v1/auth/register": 3,
            "/api/v1/checkout/create-session": 5,
        }

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/docs", "/redoc", "/openapi.json"}:
            return await call_next(request)

        try:
            redis_client = await get_redis_client()
        except Exception:
            return await call_next(request) 

        redis_client = await get_redis_client()

        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")

        key = f"rate_limit:{client_ip}:{request.url.path}"
        limit_for_path = self.custom_limits.get(request.url.path, self.default_limit)

        try:
            current = await redis_client.get(key)
            current_count = int(current) if current else 0

            if current_count >= limit_for_path:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please retry later."},
                    headers={"Retry-After": str(self.window_seconds)},
                )

            await redis_client.incr(key)
            if current_count == 0:
                await redis_client.expire(key, self.window_seconds)

        except Exception:
            pass

        return await call_next(request)