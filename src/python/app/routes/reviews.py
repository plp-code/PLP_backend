from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.dependencies import get_current_user
from src.python.app.models import User
from src.python.app.schemas import ReviewListResponse, ReviewCreate

router = APIRouter()


@router.get("/{location_id}", response_model=ReviewListResponse)
async def get_reviews(
    location_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews for the current location."""
    reviews = await crud.reviews.get_reviews_by_store_id(db, location_id=location_id)
    return ReviewListResponse(reviews=reviews, total=len(reviews))


@router.post("/{location_id}", status_code=status.HTTP_201_CREATED)
async def create_review(
    location_id: int,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new review for the specified location."""
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

    review = await crud.reviews.create_review(
        db=db,
        location_id=location_id,
        user_id=current_user.id,
        payload=payload,
        categories=categories,
    )

    return {"message": "Review created successfully", "review_id": review.id}