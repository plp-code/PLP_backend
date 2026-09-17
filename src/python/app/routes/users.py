from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.dependencies import get_current_user
from src.python.app.models import User
from src.python.app.schemas.user import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user."""
    return current_user

@router.put("/me", response_model=UserRead)
async def deactivate_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Deactivate current user account."""
    user = await crud.users.deactivate_user(db, current_user)
    return user
    