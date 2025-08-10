import json
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import settings
from app.exceptions import CacheError


class CacheService:
    def __init__(self, redis_url: str):
        self._client = redis.from_url(redis_url, decode_responses=True)

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[redis.Redis, None]:
        try:
            yield self._client
        except RedisError as e:
            raise CacheError(f"Redis operation failed: {e}")

    async def get(self, key: str) -> Optional[Any]:
        async with self.get_client() as client:
            value = await client.get(key)
            return json.loads(value) if value else None

    async def set(self, key: str, value: Any, expire: int = 3600) -> None:
        async with self.get_client() as client:
            await client.set(key, json.dumps(value), ex=expire)

    async def close(self) -> None:
        await self._client.close()


cache_service = CacheService(str(settings.REDIS_URL))
