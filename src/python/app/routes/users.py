from fastapi import APIRouter, Depends

from src.python.app import crud
from src.python.app.core.dependencies import get_current_user
from src.python.app.models import User
from src.python.app.schemas.user import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user."""
    return current_user

@router.put("/me", response_model=UserRead)
async def deactivate_user(current_user: User = Depends(get_current_user)) -> User:
    """Deactivate current user account."""
    user = await crud.user.deactivate_user(current_user.id)
    return user
    