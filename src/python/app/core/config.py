from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE_SECONDS: int = 1800
    DB_SSL_REQUIRED: bool = False
    
    
    # Redis
    # Off by default: rate limiting falls back to in-memory counting, which is
    # correct for a single process/container. Turn on when running multiple
    # workers or containers that must share limit counters.
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_TIMEOUT: int = 5
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120
    # How to find the real client IP behind the proxy.
    # TRUSTED_PROXY_IP_HEADER: a header the proxy SETS (overwrites), e.g.
    #   "do-connecting-ip". Used first when present.
    # TRUSTED_PROXY_HOPS: otherwise, how many trusted proxies APPEND to
    #   X-Forwarded-For; the client is that many entries from the right.
    #   0 = ignore X-Forwarded-For and use the socket peer.
    TRUSTED_PROXY_IP_HEADER: str | None = None
    TRUSTED_PROXY_HOPS: int = 1

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # Google Places API
    GOOGLE_PLACES_API_KEY: str

    # Email
    RESEND_API_KEY: str
    EMAIL_FROM: str 

    # App
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"


    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
