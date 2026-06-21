from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.python.app.core.database import get_db
from src.python.app.core.jwt import decode_access_token 
from src.python.app.models import User


def get_token_from_cookie(request: Request) -> str | None:
    token_str = request.cookies.get("access_token")
    if not token_str:
        return None
    if token_str.startswith("Bearer "):
        return token_str.split(" ")[1]
    return token_str


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = get_token_from_cookie(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token, expected_type="access")
        user_id = int(payload.get("sub"))

        user = await db.get(User, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    token = get_token_from_cookie(request)
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user = await db.get(User, int(payload.get("sub")))
        return user
    except Exception:
        return None