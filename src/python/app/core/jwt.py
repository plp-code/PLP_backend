import os
import jwt
import secrets

from datetime import datetime, timedelta, timezone
from fastapi import Response
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from src.python.app.core.config import settings


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token() -> tuple[str, datetime]:
    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at


def create_password_reset_token(user_email: str) -> str:
    payload = {
        "sub": user_email,
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)



def decode_password_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "password_reset":
            raise InvalidTokenError("Not a password reset token")
        return payload.get("sub")
    except (ExpiredSignatureError, InvalidTokenError):
        raise


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise InvalidTokenError("Not an access token")
        return payload
    except (ExpiredSignatureError, InvalidTokenError):
        raise
    
def set_auth_cookie(
    response: Response, 
    key: str, 
    value: str, 
    max_age: int = 15 * 60, 
    path: str = "/",
) -> None:
    is_prod = os.getenv("ENVIRONMENT") == "production"
    
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=max_age,
        path=path,
    )