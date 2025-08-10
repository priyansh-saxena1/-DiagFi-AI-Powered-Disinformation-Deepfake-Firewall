import json
from unittest.mock import AsyncMock

import pytest
from redis.asyncio import Redis

from app.exceptions import CacheError
from app.services.cache import CacheService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    client = AsyncMock(spec=Redis)
    # Ensure that the methods we call are also AsyncMocks
    client.get = AsyncMock()
    client.set = AsyncMock()
    return client


@pytest.fixture
def cache_service(mock_redis_client: AsyncMock) -> CacheService:
    # We need to manually replace the client instance inside the service
    service = CacheService(redis_url="redis://dummy")
    service._client = mock_redis_client
    return service


async def test_get_cache_hit(cache_service: CacheService, mock_redis_client: AsyncMock):
    """Test getting a value that exists in the cache."""
    key = "my-key"
    value = {"data": "my-data"}
    mock_redis_client.get.return_value = json.dumps(value)

    result = await cache_service.get(key)

    assert result == value
    mock_redis_client.get.assert_awaited_once_with(key)


async def test_get_cache_miss(cache_service: CacheService, mock_redis_client: AsyncMock):
    """Test getting a value that does not exist in the cache."""
    key = "miss-key"
    mock_redis_client.get.return_value = None

    result = await cache_service.get(key)

    assert result is None
    mock_redis_client.get.assert_awaited_once_with(key)


async def test_set_cache(cache_service: CacheService, mock_redis_client: AsyncMock):
    """Test setting a value in the cache."""
    key = "new-key"
    value = {"data": "new-data"}
    expire = 7200

    await cache_service.set(key, value, expire=expire)

    mock_redis_client.set.assert_awaited_once_with(
        key, json.dumps(value), ex=expire
    )


async def test_cache_redis_error(cache_service: CacheService, mock_redis_client: AsyncMock):
    """Test that a RedisError is wrapped in a CacheError."""
    from redis.exceptions import RedisError

    mock_redis_client.get.side_effect = RedisError("Connection failed")

    with pytest.raises(CacheError) as exc_info:
        await cache_service.get("any-key")

    assert "Redis operation failed" in str(exc_info.value)
