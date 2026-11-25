import httpx
import logging
import asyncio
import difflib

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.python.app.models.clothing_categories import ClothingCategory
from src.python.app.models.location import Location
from src.python.app.models.review_category import ReviewCategory
from src.python.app.models.reviews import Review
from src.python.app.models.location_hours import LocationHours
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


def _category_filter(category_slugs: list[str]):
    """True for locations with at least one visible review tagged with any of the slugs.

    Uses EXISTS (not a join) so a location with several matching reviews isn't duplicated.
    """
    return exists().where(
        Review.location_id == Location.id,
        Review.is_hidden.is_(False),
        ReviewCategory.review_id == Review.id,
        ReviewCategory.category_id == ClothingCategory.id,
        ClothingCategory.slug.in_(category_slugs),
    )


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _apply_filters(query, search: str | None, category_slugs: list[str] | None):
    if search and search.strip():
        pattern = f"%{_escape_like(search.strip())}%"
        query = query.where(
            Location.name.ilike(pattern, escape="\\")
            | Location.neighborhood.ilike(pattern, escape="\\")
        )
    if category_slugs:
        query = query.where(_category_filter(category_slugs))
    return query


async def resolve_category_filter(
    db: AsyncSession, map_id: int, category_slugs: list[str]
) -> tuple[list[str], bool]:
    """Decide which category slugs to actually filter by.

    Returns (effective_slugs, fell_back). If no location in the map matches the
    requested categories, the filter is dropped (everything renders) and
    fell_back is True. Decided per map, not per page, so pagination and pins agree.
    """
    if not category_slugs:
        return [], False
    matched = await db.scalar(
        select(
            exists().where(Location.map_id == map_id, _category_filter(category_slugs))
        )
    )
    if matched:
        return category_slugs, False
    return [], True


async def get_by_map(
    db: AsyncSession,
    map_id: int,
    search: str | None = None,
    category_slugs: list[str] | None = None,
) -> list[Location]:
    query = select(Location).where(Location.map_id == map_id)
    query = _apply_filters(query, search, category_slugs)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_by_map_paginated(
    db: AsyncSession,
    map_id: int,
    offset: int,
    limit: int,
    search: str | None = None,
    category_slugs: list[str] | None = None,
) -> list[Location]:
    """Get locations for a specific map with pagination and optional filters."""
    query = (
        select(Location)
        .where(Location.map_id == map_id)
        .options(selectinload(Location.hours))
    )
    query = _apply_filters(query, search, category_slugs)
    result = await db.execute(query.order_by(Location.id).offset(offset).limit(limit))
    return list(result.scalars().all())


async def create_location(
    db: AsyncSession,
    map_id: int,
    name: str,
    latitude: float,
    longitude: float,
    min_price: int | None = None,
    max_price: int | None = None,
    price_level: int | None = None,
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


TEXT_URL = "https://places.googleapis.com/v1/places:searchText"
NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
MAX_RETRIES = 4  # backoff: 1s, 2s, 4s between attempts


def _headers(field_mask: str) -> dict:
    return {
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": field_mask,
    }


def _name_score(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


async def _post(client: httpx.AsyncClient, url: str, field_mask: str, body: dict) -> httpx.Response:
    """POST with retry on 429. Returns the last response either way."""
    delay = 1.0
    for attempt in range(MAX_RETRIES):
        resp = await client.post(url, headers=_headers(field_mask), json=body)
        if resp.status_code != 429 or attempt == MAX_RETRIES - 1:
            return resp
        logger.warning(f"429 from Google Places, retrying in {delay:.0f}s")
        await asyncio.sleep(delay)
        delay *= 2
    return resp


async def _search_text(client: httpx.AsyncClient, name: str, lat: float, lng: float) -> str | None:
    resp = await _post(
        client, TEXT_URL, "places.id",
        {
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
    logger.info(f"Text search status={resp.status_code} places={len(data.get('places', []))}")

    if resp.status_code != 200:
        logger.warning(f"Google Places error: {resp.status_code} - {data.get('error', {}).get('message', data)}")
        return None

    places = data.get("places", [])
    return places[0]["id"] if places else None


async def _search_nearby(
    client: httpx.AsyncClient,
    name: str,
    lat: float,
    lng: float,
    radius_m: float = 75.0,
    min_score: float = 0.45,
) -> str | None:
    resp = await _post(
        client, NEARBY_URL, "places.id,places.displayName",
        {
            "maxResultCount": 10,
            "rankPreference": "DISTANCE",
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": radius_m,
                }
            },
        },
    )
    data = resp.json()
    logger.info(f"Nearby search status={resp.status_code} places={len(data.get('places', []))}")

    if resp.status_code != 200:
        logger.warning(f"Google Places nearby error: {resp.status_code} - {data.get('error', {}).get('message', data)}")
        return None

    places = data.get("places", [])
    if not places:
        return None

    scored = [
        (_name_score(name, p.get("displayName", {}).get("text", "")), p)
        for p in places
    ]
    best_score, best = max(scored, key=lambda t: t[0])

    if best_score >= min_score:
        logger.info(f"Nearby match '{best['displayName']['text']}' score={best_score:.2f}")
        return best["id"]
    if len(places) == 1:
        return places[0]["id"]

    logger.warning(f"Ambiguous nearby results for '{name}', skipping")
    return None


async def fetch_google_place_id(name: str, lat: float, lng: float) -> str | None:
    """Fetch a Google Place ID: text search first, coordinate search as fallback."""
    logger.info(f"Google Places lookup: name='{name}' lat={lat} lng={lng}")

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            place_id = await _search_text(client, name, lat, lng)
            if place_id:
                logger.info(f"Found place_id (text): {place_id}")
                return place_id

            logger.warning(f"No text results for '{name}', trying coordinates")
            place_id = await _search_nearby(client, name, lat, lng)
            if place_id:
                logger.info(f"Found place_id (nearby): {place_id}")
                return place_id

            logger.warning(f"No results for '{name}'")
            return None
        except Exception as e:
            logger.error(f"Google Places request failed: {e}")
            return None