from fastapi import APIRouter, Depends

from app.api.deps import  get_current_user
from app.db.models import User
from app.schemas.user import UserResponse

router = APIRouter()
    
@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user