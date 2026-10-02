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


def create_email_verification_token(email: str) -> str:
    return jwt.encode(
        {"sub": email, "purpose": "verify_email",
         "exp": datetime.now(timezone.utc) + timedelta(hours=24)},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    

def decode_email_verification_token(email: str) -> str:
    try:
        payload = jwt.decode(email, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "verify_email":
            raise InvalidTokenError("Not an email verification token")
        return payload.get("sub")
    except (ExpiredSignatureError, InvalidTokenError):
        raise



def create_password_reset_token(email: str) -> tuple[str, str]:
    jti = secrets.token_urlsafe(16)
    payload = {
        "sub": email,
        "type": "password_reset",
        "jti": jti,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def decode_password_reset_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "password_reset":
            raise InvalidTokenError("Not a password reset token")
        return {"email": payload.get("sub"), "jti": payload.get("jti")}
    except (ExpiredSignatureError, InvalidTokenError):
        raise


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise InvalidTokenError("Not an access token")
        return payload
    except (ExpiredSignatureError, InvalidTokenError):
        raise
    
    
def set_auth_cookie(response, key, value, max_age: int = 15 * 60, path: str = "/") -> None:
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