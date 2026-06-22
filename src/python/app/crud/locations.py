from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.python.app.models.location import Location
from src.python.app.models.location_hours import LocationHours
from src.python.app.models.enums import PriceLevel
from src.python.app.schemas.location import LocationHoursCreate


async def get_location_by_id(db: AsyncSession, location_id: int) -> Location | None:
    result = await db.execute(
        select(Location)
        .where(Location.id == location_id)
        .options(selectinload(Location.hours))
    )
    return result.scalar_one_or_none()


async def get_by_map(db: AsyncSession, map_id: int) -> list[Location]:
    result = await db.execute(select(Location).where(Location.map_id == map_id))
    return list(result.scalars().all())


async def get_by_map_paginated(
    db: AsyncSession, map_id: int, offset: int, limit: int
) -> list[Location]:
    result = await db.execute(
        select(Location)
        .where(Location.map_id == map_id)
        .options(selectinload(Location.hours))  # eager-load so LocationRead can serialize hours
        .order_by(Location.id)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_location(
    db: AsyncSession,
    map_id: int,
    name: str,
    latitude: float,
    longitude: float,
    min_price: int | None = None,
    max_price: int | None = None,
    price_level: PriceLevel | None = None,
    description: str | None = None,
    hours: list[LocationHoursCreate] | None = None,
) -> Location:
    location = Location(
        map_id=map_id,
        name=name,
        latitude=latitude,
        longitude=longitude,
        min_price=min_price,
        max_price=max_price,
        price_level=price_level,
        description=description,
        hours=[
            LocationHours(
                day_of_week=h.day_of_week,
                open_time=h.open_time,
                close_time=h.close_time,
                is_closed=h.is_closed,
            )
            for h in (hours or [])
        ],
    )
    db.add(location)
    await db.flush()
    return location


async def delete_location(db: AsyncSession, location: Location) -> None:
    await db.delete(location)
    await db.flush()
