from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.security import decode_token 
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

def get_token_from_cookie(request: Request) -> str:
    """Helper to safely extract and strip the token from the cookie."""
    token_str = request.cookies.get("access_token")
    if not token_str:
        return None
    if token_str.startswith("Bearer "):
        return token_str.split(" ")[1]
    return token_str

def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    token = get_token_from_cookie(request)
    if not token:
        return None 
    
    try:
        payload = decode_token(token, expected_type="access")
        user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
        return user
    except Exception:
        return None

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Checks the JWT token sent by the client to authenticate API requests.
    """
    token = get_token_from_cookie(request)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload.get("sub"))
        
        user = UserService.get_profile_with_maps(db, user_id=user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return user
        
    except HTTPException as he:
        raise he
        
    except Exception as e:
        print(f"DEBUG AUTH ERROR: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )