from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.python.app.crud.tokens import revoke_all_user_tokens
from src.python.app.models.user import User
from src.python.app.core.jwt import create_password_reset_token



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


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_or_create_pending_user(db: AsyncSession, email: str) -> User:
    """Resolve an email to a user, creating a passwordless unverified one if needed.

    Does not commit, mint tokens, or produce email args. Safe to call from flows
    (like waitlist join) that must never trigger a set-password email.
    """
    email = _normalize_email(email)
    user = await get_user_by_email(db, email)
    if user is None:
        try:
            async with db.begin_nested():
                user = await create_pending_user(db, email)
        except IntegrityError:
            user = await get_user_by_email(db, email)
            if user is None:
                raise
    return user


async def get_or_create_pending(
    db: AsyncSession, email: str
) -> tuple[User, tuple[str, str, bool] | None]:
    """Resolve a guest-checkout email to a user without committing.

    Returns (user, email_args). email_args is (email, token, has_password) when a
    set-password email must be sent after the caller commits: for a brand-new
    pending account, or for an existing unverified account (a possible squatter),
    so whoever controls the inbox can claim it.
    """
    user = await get_or_create_pending_user(db, email)
    if user.is_verified:
        return user, None

    email = _normalize_email(email)
    token, jti = create_password_reset_token(email)
    await set_reset_jti(db, user.id, jti)
    return user, (email, token, user.hashed_password is not None)


async def update_user_password(
    db: AsyncSession, user_id: int, new_hashed_password: str
) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user:
        user.hashed_password = new_hashed_password
        
        await revoke_all_user_tokens(db, user_id)
        
        await db.commit()
        await db.refresh(user)
        
    return user


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