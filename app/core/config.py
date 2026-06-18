from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    
    SECRET_KEY: str = "fallback_secret_key_for_emergencies" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()