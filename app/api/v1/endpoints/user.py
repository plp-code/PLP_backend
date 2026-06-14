from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi import Request
from app.core.security import decode_access_token
from app.api.deps import get_db
from app.db.models import User
from app.schemas.user import UserResponse

router = APIRouter()
    

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub") 
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        user_id_int = int(user_id_str) 
        
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = db.query(User).filter(User.id == user_id_int).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user