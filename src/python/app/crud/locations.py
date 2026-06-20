from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location


async def get_location_by_id(db: AsyncSession, location_id: int) -> Location | None:
    result = await db.execute(select(Location).where(Location.id == location_id))
    return result.scalar_one_or_none()


async def get_locations_by_map(db: AsyncSession, map_id: int) -> list[Location]:
    result = await db.execute(select(Location).where(Location.map_id == map_id))
    return list(result.scalars().all())


async def create_location(
    db: AsyncSession,
    map_id: int,
    name: str,
    latitude: float,
    longitude: float,
    min_price: int | None = None,
    max_price: int | None = None,
    open_time: time | None = None,
    close_time: time | None = None,
    price_level: int | None = None,
) -> Location:
    location = Location(
        map_id=map_id,
        name=name,
        latitude=latitude,
        longitude=longitude,
        min_price=min_price,
        max_price=max_price,
        open_time=open_time,
        close_time=close_time,
        price_level=price_level,
    )
    db.add(location)
    await db.flush()
    return location


async def delete_location(db: AsyncSession, location: Location) -> None:
    await db.delete(location)
    await db.flush()
