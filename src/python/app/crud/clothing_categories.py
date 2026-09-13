from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.clothing_categories import ClothingCategory


async def get_all_clothing_categories(db: AsyncSession) -> list[ClothingCategory]:
    result = await db.execute(select(ClothingCategory))
    return result.scalars().all()
    
    
async def get_clothing_categories_by_slugs(
    db: AsyncSession, slugs: list[str]
) -> list[ClothingCategory]:
    result = await db.execute(select(ClothingCategory).where(ClothingCategory.slug.in_(slugs)))
    return list(result.scalars().all())


async def get_clothing_categories_by_id(db: AsyncSession, ids: list[int]) -> list[ClothingCategory]:
    result = await db.execute(select(ClothingCategory).where(ClothingCategory.id.in_(ids)))
    return list(result.scalars().all())
