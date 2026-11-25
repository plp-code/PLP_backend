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
        .where(Review.location_id == location_id, Review.is_hidden.is_(False))
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
        categories=list(categories) if categories else [],
    )

    db.add(review)
    await db.flush()
    return review


async def get_user_review(
    db: AsyncSession, user_id: int, location_id: int, *, eager: bool = False
) -> Review | None:
    """The user's own review for a location, hidden or not. eager=True loads user/categories for serialization."""
    query = select(Review).where(Review.user_id == user_id, Review.location_id == location_id)
    if eager:
        query = query.options(selectinload(Review.user), selectinload(Review.categories))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def delete_review(db: AsyncSession, review: Review) -> None:
    await db.delete(review)
    await db.flush()
