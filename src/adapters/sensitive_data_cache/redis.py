import redis.asyncio as aioredis  # type: ignore[import-untyped]

from src.ports.sensitive_data_cache import SensitiveDataCacheABC


class RedisSensitiveDataCache(SensitiveDataCacheABC):
    def __init__(self, redis_url: str, expiry_seconds: int = 300) -> None:
        self._redis_url = redis_url
        self._expiry = expiry_seconds
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if not self._redis:
            self._redis = await aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis
