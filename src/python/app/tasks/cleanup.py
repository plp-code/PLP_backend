import logging
from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.python.app.models.token import Token

logger = logging.getLogger(__name__)


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    stmt = delete(Token).where(
        or_(
            Token.expires_at < func.now(),
            Token.is_revoked.is_(True), 
        )
    )
    result = await db.execute(stmt)
    await db.commit() 
    
    count = result.rowcount
    logger.info(f"Cleaned up {count} expired/revoked tokens")
    return count