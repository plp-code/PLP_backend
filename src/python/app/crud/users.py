from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, first_name: str, last_name: str, hashed_password: str) -> User:
    user = User(email=email, first_name=first_name, last_name=last_name, hashed_password=hashed_password)
    db.add(user)
    await db.flush()
    return user


async def deactivate_user(db: AsyncSession, user: User) -> User:
    user.is_active = False
    await db.flush()
    return user
