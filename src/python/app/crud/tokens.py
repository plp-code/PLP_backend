import hashlib
from datetime import datetime

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.python.app.models.token import Token


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def store_refresh_token(
    db: AsyncSession,
    user_id: int,
    token: str,
    expires_at: datetime,
    max_active_sessions: int = 5,
) -> Token:
    query = (
        select(Token)
        .where(
            Token.user_id == user_id,
            Token.is_revoked.is_(False),
            Token.expires_at > func.now(),
        )
        .order_by(Token.created_at.desc())
    )
    result = await db.execute(query)
    active_tokens = result.scalars().all()

    if len(active_tokens) >= max_active_sessions:
        stale_tokens = active_tokens[max_active_sessions - 1:]
        for stale in stale_tokens:
            stale.is_revoked = True

    refresh = Token(
        user_id=user_id,
        token=_hash_token(token),  
        expires_at=expires_at,
    )
    db.add(refresh)
    await db.flush()
    return refresh


async def validate_refresh_token(db: AsyncSession, token: str) -> Token | None:
    result = await db.execute(
        select(Token).where(
            Token.token == _hash_token(token),
            Token.is_revoked.is_(False),
            Token.expires_at > func.now(),
        )
    )
    return result.scalar_one_or_none()


async def revoke_token(db: AsyncSession, token: str) -> None:
    result = await db.execute(
        select(Token).where(Token.token == _hash_token(token))
    )
    refresh = result.scalar_one_or_none()
    if refresh:
        refresh.is_revoked = True


async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(Token).where(Token.user_id == user_id).values(is_revoked=True)
    )
    
    
    