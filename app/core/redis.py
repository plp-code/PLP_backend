import redis
from app.core.config import settings

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
        )
        _redis_client.ping()
    return _redis_client


def close_redis_client():
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
