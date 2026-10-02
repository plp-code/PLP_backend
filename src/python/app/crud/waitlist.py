from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.waitlist_entries import WaitlistEntries
from src.python.app.models.enums import WaitlistEntriesStatus


async def create_waitlist_entry(db: AsyncSession, user_id: int, map_id: int) -> WaitlistEntries:
    waitlist_entry = WaitlistEntries(
        user_id=user_id, 
        map_id=map_id, 
        status=WaitlistEntriesStatus.PENDING
    )
    db.add(waitlist_entry)
    await db.flush()
    return waitlist_entry


async def get_waitlist_entry(db: AsyncSession, user_id: int, map_id: int):
    result = await db.execute(
        select(WaitlistEntries).where(WaitlistEntries.user_id == user_id, WaitlistEntries.map_id == map_id)
    )
    return result.scalar_one_or_none()

async def get_waitlist_by_user_and_maps(
    db: AsyncSession, user_id: int, map_ids: list[int]
) -> list[WaitlistEntries]:
    if not map_ids:
        return []
        
    query = select(WaitlistEntries).where(
        WaitlistEntries.user_id == user_id,
        WaitlistEntries.map_id.in_(map_ids)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_waitlist_entries_by_user(db: AsyncSession, user_id: int) -> list[WaitlistEntries]:
    result = await db.execute(
        select(WaitlistEntries).where(WaitlistEntries.user_id == user_id)
    )
    return list(result.scalars().all())


async def mark_joined(db: AsyncSession, user_id: int, map_id: int):
    waitlist_entry = await get_waitlist_entry(db, user_id, map_id)
    if waitlist_entry:
        waitlist_entry.status = WaitlistEntriesStatus.JOINED
        await db.flush()