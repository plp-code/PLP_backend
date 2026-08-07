from sqlalchemy import case, select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.enums import MapStatus
from src.python.app.models.map import Map
from src.python.app.models.purchase import Purchase


async def get_map_by_id(db: AsyncSession, map_id: int) -> Map | None:
    result = await db.execute(select(Map).where(Map.id == map_id))
    return result.scalar_one_or_none()


async def get_map_by_slug(db: AsyncSession, slug: str) -> Map | None:
    """Look up a map by slug regardless of ownership (used for checkout)."""
    result = await db.execute(select(Map).where(Map.slug == slug))
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
        query = query.where(Map.status != MapStatus.DROPPED)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_active_maps(
    db: AsyncSession,
    search: str | None = None,
    status: MapStatus | None = None,
    page: int = 1,
    limit: int = 5,
) -> tuple[list[Map], int]:
    base_filter = Map.status != MapStatus.DROPPED
    if status and status != MapStatus.DROPPED:
        base_filter = Map.status == status

    query = select(Map).where(base_filter)
    count_query = select(func.count()).select_from(Map).where(base_filter)

    if search:
        search_filter = or_(
            Map.name.ilike(f"%{search}%"),
            Map.region.ilike(f"%{search}%"),
            Map.description.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Map.id).offset(offset).limit(limit)
    result = await db.execute(query)
    maps = list(result.scalars().all())

    return maps, total


async def get_maps(
    db: AsyncSession, 
    search: str | None = None, 
    page: int = 1, 
    limit: int = 25
) -> tuple[list[Map], int]:
    
    status_priority = case(
        (Map.status == MapStatus.LIVE, 1),
        (Map.status == MapStatus.WAITLIST, 2),
        (Map.status == MapStatus.DROPPED, 3),
        else_=4
    )

    query = select(Map).where(Map.status != MapStatus.DROPPED)

    if search:
        query = query.where(Map.name.ilike(f"%{search}%"))

    total_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_query)).scalar_one()

    query = (
        query
        .order_by(status_priority, Map.name.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )

    result = await db.execute(query)
    return list(result.scalars().all()), total


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
    map_.status = MapStatus.DROPPED
    await db.flush()
    return map_
