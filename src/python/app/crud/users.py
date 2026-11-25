from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError
from src.python.app.crud.tokens import revoke_all_user_tokens
from src.python.app.models.user import User
from src.python.app.core.jwt import create_password_reset_token, CLAIM_TOKEN_TTL
from src.python.app.core.email import normalize_email


async def build_claim_email_args(db: AsyncSession, user: User) -> tuple[str, str] | None:
    """Issue a fresh 24h claim (set-password) token for a passwordless account.

    Returns (email, token), or None if the user already has a password. In that
    case reset_jti is left untouched so a pending forgot-password link survives.
    Does not commit.
    """
    if user.hashed_password is not None:
        return None
    email = normalize_email(user.email)
    token, jti = create_password_reset_token(email, ttl=CLAIM_TOKEN_TTL)
    await set_reset_jti(db, user.id, jti)
    return email, token


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db, email):
    email = normalize_email(email)
    if not email:
        return None
    result = await db.execute(select(User).where(func.lower(User.email) == email))
    return result.scalar_one_or_none()



async def create_user(db: AsyncSession, email: str, first_name: str, last_name: str, hashed_password: str) -> User:
    user = User(email=email, first_name=first_name, last_name=last_name, hashed_password=hashed_password)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def create_pending_user(db: AsyncSession, email: str) -> User:
    user = User(
        email=email,
        hashed_password=None,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    return user


async def get_or_create_pending_user(db: AsyncSession, email: str) -> tuple[User, bool]:
    """Resolve an email to a user, creating a passwordless unverified one if needed.

    Returns (user, created). `created` is True only when THIS call inserted the
    row; if a concurrent request won the insert race it is False.

    Does not commit, mint tokens, or produce email args. Safe to call from flows
    (like waitlist join) that must never trigger a set-password email.
    """
    email = normalize_email(email)
    if not email:
        raise ValueError("email required")
    user = await get_user_by_email(db, email)
    if user is not None:
        return user, False
    try:
        async with db.begin_nested():
            user = await create_pending_user(db, email)
    except IntegrityError:
        user = await get_user_by_email(db, email)
        if user is None:
            raise
        return user, False
    return user, True


async def deactivate_user(db: AsyncSession, user: User) -> User:
    user.is_active = False
    await db.flush()
    return user


async def set_reset_jti(db: AsyncSession, user_id: int, jti: str) -> None:
    await db.execute(
        update(User).where(User.id == user_id).values(reset_jti=jti)
    )
    await db.flush()


async def set_password_if_jti_matches(
    db: AsyncSession, user_id: int, jti: str, new_hashed_password: str
) -> bool:
    result = await db.execute(
        update(User)
        .where(User.id == user_id, User.reset_jti == jti)
        .values(
            hashed_password=new_hashed_password,
            is_verified=True,
            reset_jti=None,
            magic_link_jti=None,
        )
    )
    return result.rowcount > 0
