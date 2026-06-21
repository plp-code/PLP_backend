from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.python.app.routes.api import api_router
from src.python.app.core.config import settings
from src.python.app.core.redis import get_redis_client, close_redis_client
from src.python.app.core.rate_limit import RedisRateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis_client()
    yield
    await close_redis_client()


app = FastAPI(title="PLP Backend API", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RedisRateLimitMiddleware,
        default_limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    )

origins = [
    settings.FRONTEND_URL,
    "https://theprelovedprofessional.com",
    "https://www.theprelovedprofessional.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)