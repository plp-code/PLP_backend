from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token


async def get_token(db: AsyncSession, token: str) -> Token | None:
    result = await db.execute(select(Token).where(Token.token == token))
    return result.scalar_one_or_none()


async def create_token(db: AsyncSession, user_id: int, token: str, expires_at: datetime) -> Token:
    db_token = Token(user_id=user_id, token=token, expires_at=expires_at)
    db.add(db_token)
    await db.flush()
    return db_token


async def delete_token(db: AsyncSession, token: Token) -> None:
    await db.delete(token)
    await db.flush()


async def delete_all_user_tokens(db: AsyncSession, user_id: int) -> None:
    await db.execute(delete(Token).where(Token.user_id == user_id))
    await db.flush()
