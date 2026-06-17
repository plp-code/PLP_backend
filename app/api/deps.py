from urllib import request

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.security import decode_access_token
from app.db.models import User
from app.services.user import UserService

dynamic_token_url = f"{settings.API_V1_STR}/auth/login".strip("/")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=dynamic_token_url)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("auth_token")
    if not token:
        return None 
    
    try:
        payload = decode_access_token(token)
        user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
        return user
    except:
        return None

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Checks the JWT token sent by the client to authenticate API requests.
    """
    token = request.cookies.get("auth_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        print(f"Extracted User ID from token: {user_id}")
        user = UserService.get_profile_with_maps(db, user_id=user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return user
    except Exception as e:
        print(f"DEBUG AUTH ERROR: {e}") # <--- ADD THIS
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    