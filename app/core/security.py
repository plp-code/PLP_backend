import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

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


def create_access_token(data: dict) -> str:
    """
    Takes a dictionary (like {"sub": "test_buyer@example.com"}) and 
    cryptographically signs it into a secure JWT string.
    """
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt