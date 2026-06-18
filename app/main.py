from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.redis import get_redis_client, close_redis_client
from app.middleware.redis_rate_limit import RedisRateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_redis_client()


app = FastAPI(title="PLP Backend API", version="1.0.0", lifespan=lifespan)

if settings.RATE_LIMIT_ENABLED:
    redis_client = get_redis_client()
    app.add_middleware(
        RedisRateLimitMiddleware,
        redis_client=redis_client,
        default_limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Injects global security headers into every HTTP response.
    """
    response = await call_next(request)    
    response.headers["X-Frame-Options"] = "DENY"    
    response.headers["X-Content-Type-Options"] = "nosniff"    
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"    
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response