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
from urllib.parse import urlsplit
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


GUEST_ACCESS_TTL = timedelta(hours=24)


def set_guest_session_cookie(response: Response, user_id: int) -> None:
    """Access-only session for a passwordless guest buyer: 24h, no refresh token.

    A refresh token is only issued once the user sets a password (reset-password
    calls set_session_cookies).
    """
    access_token = create_access_token(user_id, expires_delta=GUEST_ACCESS_TTL)
    set_auth_cookie(response, "access_token", f"Bearer {access_token}",
        max_age=int(GUEST_ACCESS_TTL.total_seconds()))

    
MAGIC_LINK_TTL = timedelta(minutes=20)            # /auth/magic-link (login page)
CHECKOUT_MAGIC_LINK_TTL = timedelta(minutes=60)   # post-purchase "Your map is ready"
DEFAULT_RETURN_PATH = "/maps"                     # matches frontend lib/returnTo.ts


def safe_return_path(path: object) -> str:
    """Return `path` only if it is a same-site relative path, else the default.

    Allows "/maps/x". Rejects absolute URLs, scheme-relative "//host",
    backslashes (browsers treat "/\\host" as "//host"), and control characters
    (browsers strip tabs/newlines, so "/\\t/host" becomes "//host").
    """
    if not isinstance(path, str) or not path or len(path) > 512:
        return DEFAULT_RETURN_PATH
    if not path.startswith("/") or path.startswith("//") or "\\" in path:
        return DEFAULT_RETURN_PATH
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in path):
        return DEFAULT_RETURN_PATH
    parts = urlsplit(path)
    if parts.scheme or parts.netloc:
        return DEFAULT_RETURN_PATH
    return path


async def create_magic_link_token(
    db: AsyncSession,
    user_id: int,
    ttl: timedelta = MAGIC_LINK_TTL,
    return_to: str | None = None,
) -> str:
    """One-time login token. Replaces any previous magic_link_jti, so only the
    newest link for a user works. Does not commit."""
    jti = secrets.token_urlsafe(16)
    user = await crud.users.get_user_by_id(db, user_id)
    user.magic_link_jti = jti
    await db.flush()

    payload = {
        "sub": str(user_id),
        "type": "magic",
        "jti": jti,
        "exp": datetime.now(timezone.utc) + ttl,
    }
    if return_to is not None:
        payload["return_to"] = return_to
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def verify_and_consume_magic_link(db: AsyncSession, token: str) -> tuple[User, str]:
    """Consume a magic link. Returns (user, return_to); return_to is always a
    validated relative path (DEFAULT_RETURN_PATH when absent or unsafe)."""
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
        .values(magic_link_jti=None, is_verified=True)
    )
    if result.rowcount != 1:
        raise ValueError("This link has already been used or is invalid")

    user = await crud.users.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        await db.rollback()
        raise ValueError("Account unavailable")

    await db.commit()
    await db.refresh(user)
    return user, safe_return_path(payload.get("return_to"))
