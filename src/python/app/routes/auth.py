from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.core.email import send_password_reset_email
from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.jwt import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    decode_password_reset_token,
    set_auth_cookie,
)
from src.python.app.core.security import hash_password, verify_password
from src.python.app.schemas.auth import ForgotPasswordRequest, LoginRequest, ResetPasswordRequest
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
    existing_refresh_token: str | None = Cookie(default=None)
) -> UserRead:
    """Authenticate user and set session cookies."""
    user = await crud.users.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if existing_refresh_token:
        raw_token = (
            existing_refresh_token.split(" ")[1]
            if existing_refresh_token.startswith("Bearer ")
            else existing_refresh_token
        )
        await crud.tokens.revoke_token(db, raw_token)

    await _set_session_cookies(response, db, user.id)
    return user


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


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Initiate password reset process."""
    user = await crud.users.get_user_by_email(db, body.email)
    
    if user:
        reset_token = create_password_reset_token(user.email)
        await send_password_reset_email(user.email, reset_token)
        
    return {"message": "If the email exists, a password reset link will be sent."}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset password using the provided token and invalidate active sessions."""
    email = decode_password_reset_token(body.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid or expired password reset token."
        )

    user = await crud.users.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid or expired password reset token."
        )

    await crud.users.update_user_password(
        db, 
        user_id=user.id, 
        new_hashed_password=hash_password(body.new_password)
    )

    return {"message": "Password reset successfully. Please log in with your new password."}

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