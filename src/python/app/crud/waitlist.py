from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.waitlist import Waitlist


async def create_walitlist_entry(db: AsyncSession, user_id: int, map_id: int) -> Waitlist:
    waitlist_entry = Waitlist(user_id, map_id=map_id, status="pending")
    db.add(waitlist_entry)
    await db.flush()
    return waitlist_entry


async def get_waitlist_entry(db: AsyncSession, user_id: int, map_id: int):
    result = await db.execute(
        select(Waitlist).where(Waitlist.user_id == user_id, Waitlist.map_id == map_id)
    )
    return result.scalar_one_or_none()


async def get_waitlist_entries_by_user(db: AsyncSession, user_id: int) -> list[Waitlist]:
    result = await db.execute(
        select(Waitlist).where(Waitlist.user_id == user_id)
    )
    return list(result.scalars().all())