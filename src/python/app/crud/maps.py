from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.map import Map
from src.python.app.models.purchase import Purchase


async def get_map_by_id(db: AsyncSession, map_id: int) -> Map | None:
    result = await db.execute(select(Map).where(Map.id == map_id))
    return result.scalar_one_or_none()


async def get_owned_map_by_slug(
    db: AsyncSession, slug: str, user_id: int,
) -> Map | None:
    result = await db.execute(
        select(Map)
        .join(Purchase, Purchase.map_id == Map.id)
        .where(
            Map.slug == slug,
            Purchase.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_all_maps(db: AsyncSession, active_only: bool = True) -> list[Map]:
    query = select(Map)
    if active_only:
        query = query.where(Map.is_active == True)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_active_maps(
    db: AsyncSession,
    search: str | None = None,
    page: int = 1,
    limit: int = 25,
) -> tuple[list[Map], int]:
    query = select(Map).where(Map.is_active == True)
    count_query = select(func.count()).select_from(Map).where(Map.is_active == True)

    if search:
        search_filter = or_(
            Map.name.ilike(f"%{search}%"),
            Map.region.ilike(f"%{search}%"),
            Map.description.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    total = (await db.execute(count_query)).scalar()

    offset = (page - 1) * limit
    query = query.order_by(Map.id).offset(offset).limit(limit)
    result = await db.execute(query)
    maps = list(result.scalars().all())

    return maps, total


async def create_map(
    db: AsyncSession,
    name: str,
    slug: str,
    price: int,
    region: str | None = None,
    description: str | None = None,
) -> Map:
    map_ = Map(name=name, slug=slug, price=price, region=region, description=description)
    db.add(map_)
    await db.flush()
    return map_


async def deactivate_map(db: AsyncSession, map_: Map) -> Map:
    map_.is_active = False
    await db.flush()
    return map_
