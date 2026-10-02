import logging
import os

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from src.python.app import crud
from src.python.app.core.database import get_db
from src.python.app.core.email import send_password_reset_email, send_magic_login_email, send_email_verification
from src.python.app.core.jwt import (
    create_password_reset_token,
    decode_password_reset_token,
    decode_email_verification_token,
    create_email_verification_token,
)
from src.python.app.core.dependencies import get_current_user
from src.python.app.models import User
from src.python.app.core.security import hash_password, verify_password
from src.python.app.schemas import ForgotPasswordRequest, LoginRequest, ResetPasswordRequest, MagicLinkRequest, VerfyLinkRequest,  UserCreate, UserRead

logger = logging.getLogger(__name__)

router = APIRouter()

    
async def _send_magic_link_email_safe(email: str, token: str) -> None:
    try:
        await send_magic_login_email(email, token)
    except Exception:
        logger.exception("Failed to send magic link email")


@router.post("/magic-link")
async def request_magic_link(
    payload: MagicLinkRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await crud.users.get_user_by_email(db, payload.email)

    if user and user.hashed_password is None and user.is_active:
        token = await crud.auth.create_magic_link_token(db, user.id)
        background_tasks.add_task(_send_magic_link_email_safe, user.email, token)

    return {"status": "sent"}


@router.post("/verify-magic-link")
async def verify_magic_link(
    payload: VerfyLinkRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        user = await crud.auth.verify_and_consume_magic_link(db, payload.token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=400, detail="This link has expired or already been used.")

    await crud.auth.set_session_cookies(response, db, user.id)
    return {"status": "logged_in"}


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    existing = await crud.users.get_user_by_email(db, user_in.email)

    if existing is not None:
        if existing.hashed_password is not None:
            raise HTTPException(status_code=400, detail="Email already registered")

        token, jti = create_password_reset_token(existing.email)
        await crud.users.set_reset_jti(db, existing.id, jti)
        await db.commit()
        background_tasks.add_task(
            send_password_reset_email, existing.email, token, has_password=False
        )
        return {"status": "check_email"}

    user = await crud.users.create_user(
        db,
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        hashed_password=hash_password(user_in.password),
    )
    token = create_email_verification_token(user.email)

    await crud.auth.set_session_cookies(response, db, user.id)
    await db.commit()
    await db.refresh(user)

    background_tasks.add_task(send_email_verification, user.email, token)
    return user
    


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    existing_refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
) -> UserRead:
    """Authenticate user and set session cookies."""
    user = await crud.users.get_user_by_email(db, data.email)
    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if existing_refresh_token:
        raw_token = (
            existing_refresh_token.split(" ")[1]
            if existing_refresh_token.startswith("Bearer ")
            else existing_refresh_token
        )
        await crud.tokens.revoke_token(db, raw_token)

    await crud.auth.set_session_cookies(response, db, user.id)
    return user


@router.post("/refresh")
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> dict:
    """Refresh access token and rotate the refresh token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    token = refresh_token.split(" ")[1] if refresh_token.startswith("Bearer ") else refresh_token

    stored = await crud.tokens.validate_refresh_token(db, token)
    if not stored:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await crud.users.get_user_by_id(db, stored.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    await crud.tokens.revoke_token(db, token)          
    await crud.auth.set_session_cookies(response, db, user.id)  
    await db.commit()

    return {"message": "Token refreshed"}


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await crud.users.get_user_by_email(db, body.email)

    if user:
        token, jti = create_password_reset_token(user.email)
        await crud.users.set_reset_jti(db, user.id, jti)
        await db.commit()

        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            token,
            has_password=user.hashed_password is not None,
        )

    return {"message": "If that email has an account, a link is on its way."}

@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        payload = decode_password_reset_token(body.token)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")

    email, jti = payload.get("email"), payload.get("jti")
    if not email or not jti:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")

    user = await crud.users.get_user_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")

    success = await crud.users.set_password_if_jti_matches(
        db, user_id=user.id, jti=jti, new_hashed_password=hash_password(body.new_password)
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")

    await crud.tokens.revoke_all_user_tokens(db, user.id)
    await crud.auth.set_session_cookies(response, db, user.id)
    await db.commit()

    return {"message": "Password set successfully."}


@router.get("/reset-password/check")
async def check_reset_token(token: str, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        payload = decode_password_reset_token(token)
    except jwt.InvalidTokenError:
        return {"valid": False}

    email = payload.get("email")
    user = await crud.users.get_user_by_email(db, email) if email else None
    if not user or user.reset_jti != payload.get("jti"):
        return {"valid": False}

    return {"valid": True, "has_password": user.hashed_password is not None}


@router.post("/verify-email")
async def verify_email(
    body: VerfyLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user), 
):
    email = decode_email_verification_token(body.token) 
    if current_user.email != email:
        raise HTTPException(status_code=403, detail="Log in as the account you are verifying")
    if not current_user.is_verified:
        current_user.is_verified = True
        await db.commit()
    return {"status": "ok"}


def _clear_auth_cookies(response: Response) -> None:
    is_prod = os.getenv("ENVIRONMENT") == "production"
    response.delete_cookie(key="access_token", path="/", httponly=True, secure=is_prod, samesite="lax")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth", httponly=True, secure=is_prod, samesite="lax")


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
        await db.commit()

    _clear_auth_cookies(response)
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
            await db.commit()

    _clear_auth_cookies(response)
    return {"message": "Logged out from all devices"}
