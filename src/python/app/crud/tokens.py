from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.models.token import Token


async def store_refresh_token(
    db: AsyncSession, user_id: int, token: str, expires_at: datetime,
) -> Token:
    refresh = Token(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(refresh)
    await db.flush()
    return refresh


async def validate_refresh_token(
    db: AsyncSession, token: str,
) -> Token | None:
    result = await db.execute(
        select(Token).where(
            Token.token == token,
            Token.is_revoked == False,
            Token.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()


async def revoke_token(db: AsyncSession, token: str) -> None:
    result = await db.execute(
        select(Token).where(Token.token == token)
    )
    refresh = result.scalar_one_or_none()
    if refresh:
        refresh.is_revoked = True


async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> None:
    """Logout from all devices."""
    await db.execute(
        delete(Token).where(Token.user_id == user_id)
    )