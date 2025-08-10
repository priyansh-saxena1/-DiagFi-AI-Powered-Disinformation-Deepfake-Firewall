from unittest.mock import AsyncMock, patch

import pytest
from redis.asyncio import Redis

from app.services.rumor import RumorService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    client = AsyncMock(spec=Redis)
    client.zadd = AsyncMock()
    client.expire = AsyncMock()
    client.zremrangebyscore = AsyncMock()
    client.zcount = AsyncMock()
    return client


@pytest.fixture
def rumor_service(mock_redis_client: AsyncMock) -> RumorService:
    return RumorService(redis_client=mock_redis_client)


@patch("time.time", return_value=1700000000.0)
async def test_record_sighting(mock_time, rumor_service: RumorService, mock_redis_client: AsyncMock):
    """Test that recording a sighting adds it to a Redis sorted set."""
    topic = "test-topic"
    source = "test-source"

    await rumor_service.record_sighting(topic, source)

    expected_key = f"rumor:sightings:{topic}"
    expected_member = f"{source}:1700000000.0"

    mock_redis_client.zadd.assert_awaited_once_with(
        expected_key, {expected_member: 1700000000.0}
    )
    mock_redis_client.zremrangebyscore.assert_awaited_once_with(
        expected_key, "-inf", 1700000000.0 - 3600
    )
    mock_redis_client.expire.assert_awaited_once_with(expected_key, 3600)


@patch("time.time", return_value=1700000060.0)
async def test_get_velocity(mock_time, rumor_service: RumorService, mock_redis_client: AsyncMock):
    """Test the velocity calculation."""
    topic = "test-topic"
    window_seconds = 60

    mock_redis_client.zcount.return_value = 15  # 15 sightings in the last 60 seconds

    velocity = await rumor_service.get_velocity(topic, window_seconds=window_seconds)

    # (15 sightings / 60 seconds) * 60 seconds/minute = 15 mentions/minute
    assert velocity == 15.0

    expected_key = f"rumor:sightings:{topic}"
    mock_redis_client.zcount.assert_awaited_once_with(
        expected_key, 1700000000.0, 1700000060.0
    )
