from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.dependencies import get_current_user, get_current_user_optional
from src.python.app.models import User
from src.python.app.schemas.map import MapListResponse, MapSummary
from src.python.app.schemas.location import LocationMinimalRead, LocationRead
from src.python.app.models.map import Map

router = APIRouter()


async def get_owned_map(
    slug: str, db: AsyncSession, user: User,
) -> Map:
    """Helper function to get a map by slug that the user owns."""
    map_ = await crud.maps.get_owned_map_by_slug(db, slug, user.id)
    if not map_:
        raise HTTPException(status_code=403, detail="Access denied")
    return map_


@router.get("", response_model=MapListResponse)
async def list_maps(
    search: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """List maps with pagination and optional search. Indicates if the current user owns each map."""
    maps, total = await crud.maps.get_active_maps(
        db, search=search, page=page, limit=limit,
    )

    owned: set[int] = set()
    if current_user:
        owned = {purchase.map_id for purchase in await crud.purchases.get_purchases_by_user(db, current_user.id)}

    items = [
        MapSummary(
            id=m.id,
            name=m.name,
            slug=m.slug,
            region=m.region,
            price=m.price,
            description=m.description,
            is_purchased=m.id in owned,
        )
        for m in maps
    ]

    return MapListResponse(
        maps=items,
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


@router.get("/{slug}/locations/pins", response_model=list[LocationMinimalRead])
async def get_map_pins(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get minimal location info (pins) for a map the user owns."""
    map_ = await get_owned_map(slug, db, current_user)
    locations = await crud.locations.get_by_map(db, map_.id)
    return [LocationMinimalRead.model_validate(loc) for loc in locations]


@router.get("/{slug}/locations", response_model=list[LocationRead])
async def get_locations_paginated(
    slug: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated locations for a map the user owns."""
    map_ = await get_owned_map(slug, db, current_user)
    offset = (page - 1) * limit
    locations = await crud.locations.get_by_map_paginated(db, map_.id, offset, limit)
    return [LocationRead.model_validate(loc) for loc in locations]