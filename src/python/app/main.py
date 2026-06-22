from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, logger, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.responses import JSONResponse
import asyncio
from src.python.app.core.database import AsyncSessionLocal, get_db
from src.python.app.tasks.cleanup import cleanup_expired_tokens
from src.python.app.routes.api import api_router
from src.python.app.core.config import settings
from src.python.app.core.redis import get_redis_client, close_redis_client
from src.python.app.core.rate_limit import RedisRateLimitMiddleware

async def scheduled_cleanup():
    while True:
        await asyncio.sleep(24 * 60 * 60)  
        async with AsyncSessionLocal() as db:
            try:
                await cleanup_expired_tokens(db)
                await db.commit()
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await get_redis_client()
    except Exception:
        print("Redis not available — rate limiting disabled")
        
    cleanup_task = asyncio.create_task(scheduled_cleanup())
        
    yield
    
    cleanup_task.cancel()
    await close_redis_client()
    
app = FastAPI(title="PLP Backend API", version="1.0.0", lifespan=lifespan)

    
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"},
        )


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