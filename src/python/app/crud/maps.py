from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.map import Map


async def get_map_by_id(db: AsyncSession, map_id: int) -> Map | None:
    result = await db.execute(select(Map).where(Map.id == map_id))
    return result.scalar_one_or_none()


async def get_map_by_slug(db: AsyncSession, slug: str) -> Map | None:
    result = await db.execute(select(Map).where(Map.slug == slug))
    return result.scalar_one_or_none()


async def get_all_maps(db: AsyncSession, active_only: bool = True) -> list[Map]:
    query = select(Map)
    if active_only:
        query = query.where(Map.is_active == True)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_map(db: AsyncSession, name: str, slug: str, price: int, region: str | None = None) -> Map:
    map_ = Map(name=name, slug=slug, price=price, region=region)
    db.add(map_)
    await db.flush()
    return map_


async def deactivate_map(db: AsyncSession, map_: Map) -> Map:
    map_.is_active = False
    await db.flush()
    return map_
