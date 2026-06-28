import httpx
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.python.app.models.location import Location
from src.python.app.models.location_hours import LocationHours
from src.python.app.models.enums import PriceLevel
from src.python.app.schemas.location import LocationHoursCreate
from src.python.app.core.config import settings


logger = logging.getLogger(__name__)


async def get_location_by_id(db: AsyncSession, location_id: int) -> Location | None:
    """Get a location by its ID, including its hours."""
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
    """Get locations for a specific map with pagination."""
    result = await db.execute(
        select(Location)
        .where(Location.map_id == map_id)
        .options(selectinload(Location.hours))  
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
    """Create a new location with optional hours."""
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
    """Delete a location and its associated hours."""
    await db.delete(location)
    await db.flush()


async def fetch_google_place_id(name: str, lat: float, lng: float) -> str | None:
    """Fetch Google Place ID using Places API (New) — free for IDs only."""
    async with httpx.AsyncClient() as client:
        logger.info(f"Google Places lookup: name='{name}' lat={lat} lng={lng}")

        try:
            resp = await client.post(
                "https://places.googleapis.com/v1/places:searchText",
                headers={
                    "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
                    "X-Goog-FieldMask": "places.id",
                },
                json={
                    "textQuery": name,
                    "locationBias": {
                        "circle": {
                            "center": {"latitude": lat, "longitude": lng},
                            "radius": 500.0,
                        }
                    },
                },
            )
            data = resp.json()
            logger.info(f"Google Places response: status={resp.status_code} places={len(data.get('places', []))}")

            if resp.status_code != 200:
                logger.warning(f"Google Places error: {resp.status_code} - {data.get('error', {}).get('message', data)}")
                return None

            if data.get("places"):
                place_id = data["places"][0]["id"]
                logger.info(f"Found place_id: {place_id}")
                return place_id

            logger.warning(f"No results for '{name}'")
            return None
        except Exception as e:
            logger.error(f"Google Places request failed: {e}")
            return None