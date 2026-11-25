from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.dependencies import get_current_user
from src.python.app.models import Location, User
from src.python.app.schemas import ReviewListResponse, ReviewCreate, ReviewMine

router = APIRouter()


async def _get_location_for_buyer(db: AsyncSession, location_id: int, user: User) -> Location:
    """Return the location, or raise 404 (missing) / 403 (user hasn't bought its map)."""
    location = await db.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    if not await crud.purchases.user_owns_map(db, user.id, location.map_id):
        raise HTTPException(status_code=403, detail="Only buyers of this map can access its reviews")
    return location


@router.get("/{location_id}", response_model=ReviewListResponse)
async def get_reviews(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get visible reviews for a location. Buyers of the location's map only."""
    await _get_location_for_buyer(db, location_id, current_user)
    reviews = await crud.reviews.get_reviews_by_store_id(db, location_id=location_id)
    return ReviewListResponse(reviews=reviews, total=len(reviews))


@router.get("/{location_id}/me", response_model=ReviewMine | None)
async def get_my_review(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The caller's own review for this location, or null. Includes hidden (moderated)
    reviews and works even if the purchase was refunded, so the author can always see/delete it."""
    return await crud.reviews.get_user_review(db, current_user.id, location_id, eager=True)


@router.post("/{location_id}", status_code=status.HTTP_201_CREATED)
async def create_review(
    location_id: int,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a review (one per user per location). Buyers of the location's map only."""
    await _get_location_for_buyer(db, location_id, current_user)

    already = HTTPException(status_code=409, detail="You've already reviewed this location")

    if await crud.reviews.get_user_review(db, current_user.id, location_id):
        raise already

    categories = []

    if payload.category_slugs:
        categories = await crud.clothing_categories.get_clothing_categories_by_slugs(
            db=db, slugs=payload.category_slugs
        )

        found_slugs = {c.slug for c in categories}
        missing_slugs = set(payload.category_slugs) - found_slugs

        if missing_slugs:
            raise HTTPException(
                status_code=400,
                detail=f"Category slugs not found: {sorted(missing_slugs)}",
            )

    try:
        review = await crud.reviews.create_review(
            db=db,
            location_id=location_id,
            user_id=current_user.id,
            payload=payload,
            categories=categories,
        )
    except IntegrityError:
        # Race: a concurrent request inserted first; uq_reviews_user_location caught it.
        await db.rollback()
        if await crud.reviews.get_user_review(db, current_user.id, location_id):
            raise already
        raise

    return {"message": "Review created successfully", "review_id": review.id}


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_review(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete the current user's own review for this location."""
    review = await crud.reviews.get_user_review(db, current_user.id, location_id)
    if not review:
        raise HTTPException(status_code=404, detail="You haven't reviewed this location")
    await crud.reviews.delete_review(db, review)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
