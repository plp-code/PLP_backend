from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.schemas import CategoriesRead


router = APIRouter()


@router.get("", response_model=list[CategoriesRead])
async def get_clothing_categories(
    db: AsyncSession = Depends(get_db),
):
    """Get all clothing categories."""
    categories = await crud.clothing_categories.get_all_clothing_categories(db)
    return categories

