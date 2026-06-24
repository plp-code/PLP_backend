import logging

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.python.app.models.token import Token

logger = logging.getLogger(__name__)


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    result = await db.execute(
        delete(Token).where(Token.expires_at < func.now())
    )
    count = result.rowcount
    logger.info(f"Cleaned up {count} expired tokens")
    return count