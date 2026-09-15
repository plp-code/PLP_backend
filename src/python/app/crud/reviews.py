from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.python.app.models.reviews import Review
from src.python.app.models.clothing_categories import ClothingCategory
from src.python.app.schemas.review import ReviewCreate


async def get_reviews_by_store_id(db: AsyncSession, location_id: int) -> list[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.location_id == location_id)
        .options(
            selectinload(Review.user),
            selectinload(Review.categories),
        )
    )
    return result.scalars().all()


async def create_review(
    db: AsyncSession,
    location_id: int,
    user_id: int,
    payload: ReviewCreate,
    categories: Sequence[ClothingCategory] | None = None,
) -> Review:
    review = Review(
        user_id=user_id,
        location_id=location_id,
        experience=payload.experience,
        item_purchased=payload.item_purchased,
        price_paid=payload.price_paid,
        is_hidden=getattr(payload, "is_hidden", False),
        categories=list(categories) if categories else [],
    )

    db.add(review)
    await db.commit()    

    return review