from fastapi import APIRouter, Depends

from src.python.app.core.dependencies import get_current_user
from src.python.app.models import User
from src.python.app.schemas.user import UserMe

router = APIRouter()


@router.get("/me", response_model=UserMe)
async def read_current_user(current_user: User = Depends(get_current_user)) -> UserMe:
    """Get current authenticated user."""
    return UserMe.from_user(current_user)
