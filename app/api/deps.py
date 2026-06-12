from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.user import UserService

dynamic_token_url = f"{settings.API_V1_STR}/auth/login".strip("/")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=dynamic_token_url)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """
    Checks the JWT token sent by the client to authenticate API requests.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
            
        token_user_id = int(user_id_str)
        
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = UserService.get_profile_with_maps(db, user_id=token_user_id)
    if user is None:
        raise credentials_exception
        
    return user