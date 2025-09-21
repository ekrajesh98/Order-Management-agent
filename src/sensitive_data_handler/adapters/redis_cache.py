import json
from typing import List

import redis.asyncio as aioredis  # type: ignore[import-untyped]

from ..ports.data_cache_port import SensitiveDataCacheABC


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

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """
        Store the mapping from redacted key to original text.
        If the key already exists, simply reset its TTL.
        """
        client = await self._get_redis()
        expire = ttl if ttl is not None else self._expiry
        data = json.dumps(value)
        if await client.exists(key):
            await client.expire(key, expire)
        else:
            await client.set(name=key, value=data, ex=expire)

    async def get(self, key: str) -> str | None:
        """
        Retrieve the original text for a given redacted key.
        """
        client = await self._get_redis()
        data = await client.get(name=key)
        if data is None:
            return None
        return json.loads(data)

    async def delete(self, key: str) -> bool:
        """
        Delete a mapping from the cache.
        """
        client = await self._get_redis()
        count = await client.delete(key)
        return count > 0

    async def exists(self, key: str) -> bool:
        """
        Check whether a redacted key exists in the cache.
        """
        client = await self._get_redis()
        return await client.exists(key) == 1

    async def keys(self, pattern: str | None = None) -> List[str]:
        """
        List all redacted-string keys currently stored in the cache.
        """
        client = await self._get_redis()
        match = pattern if pattern is not None else "*"
        # Use scan to avoid blocking
        cursor = "0"
        keys: List[str] = []
        while cursor != 0:
            cursor, batch = await client.scan(cursor=cursor, match=match)
            keys.extend(batch)
        return keys

    async def clear(self) -> None:
        """
        Remove all entries from the cache.
        """
        client = await self._get_redis()
        await client.flushdb()

    async def set_many_under(
        self, parent_key: str, kv: dict[str, str], ttl: int = 28_800
    ) -> None:
        """
        Merge `kv` into the JSON dict stored at `parent_key`.
        Fields in `kv` overwrite existing ones with the same name.
        Existing fields not in `kv` are preserved.
        """
        client = await self._get_redis()
        expire = ttl if ttl is not None else self._expiry
        raw = await client.get(parent_key)
        try:
            data: dict[str, str] = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {}

        data.update(kv)

        await client.set(parent_key, json.dumps(data), ex=expire)
