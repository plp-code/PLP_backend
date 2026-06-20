from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase import Purchase


async def get_purchase(db: AsyncSession, user_id: int, map_id: int) -> Purchase | None:
    result = await db.execute(
        select(Purchase).where(Purchase.user_id == user_id, Purchase.map_id == map_id)
    )
    return result.scalar_one_or_none()


async def get_purchases_by_user(db: AsyncSession, user_id: int) -> list[Purchase]:
    result = await db.execute(select(Purchase).where(Purchase.user_id == user_id))
    return list(result.scalars().all())


async def create_purchase(db: AsyncSession, user_id: int, map_id: int, transaction_id: int) -> Purchase:
    purchase = Purchase(user_id=user_id, map_id=map_id, transaction_id=transaction_id)
    db.add(purchase)
    await db.flush()
    return purchase


async def user_owns_map(db: AsyncSession, user_id: int, map_id: int) -> bool:
    result = await get_purchase(db, user_id, map_id)
    return result is not None
