from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.jwt import (
    create_access_token,
    create_refresh_token,
    set_auth_cookie,
)
from src.python.app.core.security import hash_password, verify_password
from src.python.app.schemas.auth import LoginRequest
from src.python.app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Register a new user and set session cookies."""
    if await crud.users.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await crud.users.create_user(
        db,
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        hashed_password=hash_password(user_in.password),
    )

    await _set_session_cookies(response, db, user.id)
    return user


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate user and set session cookies."""
    user = await crud.users.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    await _set_session_cookies(response, db, user.id)
    return {"message": "Logged in"}


@router.post("/refresh")
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> dict:
    """Refresh access token using refresh token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    token = refresh_token.split(" ")[1] if refresh_token.startswith("Bearer ") else refresh_token

    stored = await crud.tokens.validate_refresh_token(db, token)
    if not stored:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token = create_access_token(stored.user_id)
    set_auth_cookie(response, "access_token", f"Bearer {access_token}")

    return {"message": "Token refreshed"}


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> dict:
    """Logout user by revoking the refresh token."""
    if refresh_token:
        token = refresh_token.split(" ")[1] if refresh_token.startswith("Bearer ") else refresh_token
        await crud.tokens.revoke_token(db, token)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/v1/auth") 
    return {"message": "Logged out"}


@router.post("/logout-all")
async def logout_all(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> dict:
    """Logout from all devices."""
    if refresh_token:
        token = refresh_token.split(" ")[1] if refresh_token.startswith("Bearer ") else refresh_token
        stored = await crud.tokens.validate_refresh_token(db, token)
        if stored:
            await crud.tokens.revoke_all_user_tokens(db, stored.user_id)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    return {"message": "Logged out from all devices"}

async def _set_session_cookies(response: Response, db: AsyncSession, user_id: int) -> None:
    access_token = create_access_token(user_id)
    refresh_token, expires_at = create_refresh_token()

    await crud.tokens.store_refresh_token(
        db,
        user_id=user_id,
        token=refresh_token,
        expires_at=expires_at,
    )

    set_auth_cookie(response, "access_token", f"Bearer {access_token}")
    set_auth_cookie(response, "refresh_token", f"Bearer {refresh_token}",
        max_age=7 * 24 * 60 * 60,
        path="/api/v1/auth",
    )