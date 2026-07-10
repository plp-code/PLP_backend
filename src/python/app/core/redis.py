from redis.asyncio import Redis
from src.python.app.core.config import settings

_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
        )
        # Only cache the client once we've confirmed it's reachable, so a failed
        # ping doesn't leave a broken client that stalls every later request.
        await client.ping()
        _redis_client = client
    return _redis_client


async def close_redis_client():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None