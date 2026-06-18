import os

import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from fastapi import HTTPException, Response, status

def get_password_hash(password: str) -> str:
    """
    Takes a raw password, converts it to bytes, and scrambles it 
    into a secure string for the database.
    """
    password_bytes = password.encode('utf-8')
    
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(password=password_bytes, salt=salt)
        
    return hashed_password_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Takes the raw password from login, hashes it, and checks if it 
    matches the hash stored in the database.
    """
    plain_password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(password=plain_password_bytes, hashed_password=hashed_password_bytes)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Takes a dictionary (like {"sub": "test_buyer@example.com"}) and 
    cryptographically signs it into a secure JWT string.
    """
    to_encode = data.copy()
    to_encode.update({"type": "access"})
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Similar to create_access_token but with a longer expiration time.
    Used to issue new access tokens without requiring the user to log in again.
    """
    to_encode = data.copy()
    to_encode.update({"type": "refresh"})

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str, expected_type: str) -> dict:
    """
    Generalized token decoder that checks for token type (access or refresh).
    """
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}."
            )
            
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
        
def set_auth_cookie(response: Response, key: str, value: str, max_age: int = 15 * 60, path: str = "/"):
    is_prod = os.getenv("ENVIRONMENT") == "production"
    
    response.set_cookie(
        key=key,
        value=value,
        httponly=True, 
        samesite="lax",
        secure=is_prod,
        path=path,
        max_age=max_age
    )
    