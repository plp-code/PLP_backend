from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.python.app.models.enums import MapStatus
from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.dependencies import get_current_user, get_current_user_optional
from src.python.app.models import User
from src.python.app.schemas import MapListResponse, MapSummary, LocationMinimalRead, LocationRead, WaitlistJoinRequest
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
    status: MapStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=5, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    maps, total = await crud.maps.get_active_maps(
        db, search=search, status=status, page=page, limit=limit
    )

    owned: set[int] = set()
    waitlisted: set[int] = set()

    if current_user and maps:
        page_map_ids = [m.id for m in maps]
        purchases = await crud.purchases.get_purchases_by_user_and_maps(
            db, user_id=current_user.id, map_ids=page_map_ids
        )
        owned = {p.map_id for p in purchases}

        entries = await crud.waitlist.get_waitlist_by_user_and_maps(
            db, user_id=current_user.id, map_ids=page_map_ids
        )
        waitlisted = {e.map_id for e in entries}

    items = [
        MapSummary(
            id=m.id,
            name=m.name,
            slug=m.slug,
            region=m.region,
            price=m.price,
            description=m.description,
            status=m.status,
            is_purchased=m.id in owned,
            is_waitlisted=m.id in waitlisted,
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
    
    
@router.put("/{slug}/join-waitlist", response_model=dict)
async def join_waitlist(
    slug: str,
    body: WaitlistJoinRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Join the waitlist for a map. Logged-in users use their account; guests supply an email."""
    map_ = await crud.maps.get_map_by_slug(db, slug)
    if not map_:
        raise HTTPException(status_code=404, detail="Map not found")

    result = {"message": f"Successfully joined the waitlist for {map_.name}"}

    if current_user:
        if await crud.waitlist.get_waitlist_entry(db, current_user.id, map_.id):
            raise HTTPException(status_code=400, detail="Already on the waitlist for this map")
        await crud.waitlist.create_waitlist_entry(db, current_user.id, map_.id)
        return result

    if not body or not body.email:
        raise HTTPException(status_code=422, detail="Email is required")

    user = await crud.users.get_or_create_pending_user(db, body.email)

    if not await crud.purchases.user_owns_map(db, user.id, map_.id):
        try:
            async with db.begin_nested():
                await crud.waitlist.create_waitlist_entry(db, user.id, map_.id)
        except IntegrityError:
            pass  

    await db.commit()
    return result


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


# @router.put("/{slug}/locations/google-place-ids")
# async def update_google_place_ids(
#     slug: str,
#     db: AsyncSession = Depends(get_db),
#     # x_admin_key: str = Header(...),
# ):
#     """Batch update Google Place IDs for all locations in a map."""
#     # if x_admin_key != settings.ADMIN_API_KEY:
#     #     raise HTTPException(status_code=403, detail="Forbidden")

#     map_ = await crud.maps.get_map_by_slug(db, slug)
#     if not map_:
#         raise HTTPException(status_code=404, detail="Map not found")

#     locations = await crud.locations.get_by_map(db, map_.id)

#     updated = 0
#     skipped = 0
#     failed = 0

#     for location in locations:
#         if location.google_place_id:
#             skipped += 1
#             continue

#         place_id = await crud.locations.fetch_google_place_id(
#             location.name, location.latitude, location.longitude,
#         )

#         if place_id:
#             location.google_place_id = place_id
#             updated += 1
#         else:
#             failed += 1

#     return {
#         "map": map_.name,
#         "total": len(locations),
#         "updated": updated,
#         "skipped": skipped,
#         "failed": failed,
#     }