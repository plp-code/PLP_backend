from fastapi import Response
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from src.python.app.models.user import User
from src.python.app.core.config import settings
from src.python.app.core.security import hash_password
from src.python.app.core.jwt import decode_token, create_access_token, create_refresh_token, set_auth_cookie
from src.python.app import crud

import secrets
from datetime import datetime, timedelta, timezone
import jwt


async def set_session_cookies(response: Response, db: AsyncSession, user_id: int) -> None:
    access_token = create_access_token(user_id)
    refresh_token, expires_at = create_refresh_token()

    await crud.tokens.store_refresh_token(
        db, user_id=user_id, token=refresh_token, expires_at=expires_at,
    )

    set_auth_cookie(response, "access_token", f"Bearer {access_token}",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    set_auth_cookie(response, "refresh_token", f"Bearer {refresh_token}",
        max_age=7 * 24 * 60 * 60, path="/api/v1/auth")
    
    
async def create_magic_link_token(db: AsyncSession, user_id: int) -> str:
    jti = secrets.token_urlsafe(16)
    user = await crud.users.get_user_by_id(db, user_id)
    user.magic_link_jti = jti
    await db.flush()

    payload = {
        "sub": str(user_id),
        "type": "magic",
        "jti": jti,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=20),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def verify_and_consume_magic_link(db: AsyncSession, token: str) -> User:
    payload = decode_token(token)
    if payload.get("type") != "magic":
        raise ValueError("Invalid token type")

    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub:
        raise ValueError("Malformed token")
    user_id = int(sub)

    result = await db.execute(
        update(User)
        .where(User.id == user_id, User.magic_link_jti == jti)
        .values(magic_link_jti=None)
    )
    if result.rowcount != 1:
        raise ValueError("This link has already been used or is invalid")

    user = await crud.users.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        await db.rollback()
        raise ValueError("Account unavailable")

    await db.commit()
    await db.refresh(user)
    return user
