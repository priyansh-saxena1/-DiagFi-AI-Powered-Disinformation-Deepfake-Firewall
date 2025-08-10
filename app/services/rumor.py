import asyncio
import random
import time
from collections import deque
from typing import Deque

import aiostream
from redis.asyncio import Redis

from app.services.cache import cache_service


class RumorService:
    def __init__(self, redis_client: Redis):
        self._redis = redis_client
        # In-memory cache for recent velocities to avoid hitting Redis too often
        self._velocity_cache: Deque[tuple[str, float, float]] = deque(maxlen=100)

    async def record_sighting(self, topic: str, source: str) -> None:
        key = f"rumor:sightings:{topic}"
        timestamp = time.time()
        # The score is the timestamp, allowing time-series queries
        await self._redis.zadd(key, {f"{source}:{timestamp}": timestamp})
        # Automatically trim the set to keep it from growing indefinitely
        await self._redis.zremrangebyscore(key, "-inf", timestamp - 3600)  # Keep 1 hour
        await self._redis.expire(key, 3600)

    async def get_velocity(self, topic: str, window_seconds: int = 60) -> float:
        key = f"rumor:sightings:{topic}"
        now = time.time()
        start_time = now - window_seconds

        # ZCOUNT is more efficient than fetching all and filtering in Python
        count = await self._redis.zcount(key, start_time, now)
        velocity = (count / window_seconds) * 60  # Mentions per minute
        self._velocity_cache.append((topic, now, velocity))
        return velocity


async def _simulated_feed(name: str, interval: float, topics: list[str]):
    """Async generator simulating a feed like RSS or a social media stream."""
    while True:
        await asyncio.sleep(interval)
        yield name, random.choice(topics)


async def poll_feeds_background_task(rumor_service: RumorService, alert_threshold: int = 10):
    """A background task that polls various feeds and checks for rumor velocity."""
    topics = ["election-fraud", "crypto-scam", "celebrity-gossip", "health-misinfo"]

    # Create a merged stream of all sources
    combined_feeds = aiostream.stream.merge(
        _simulated_feed("RSS-Feed", 7.0, topics),
        _simulated_feed("X-Stream", 2.5, topics),
        _simulated_feed("Telegram-Channel", 4.0, topics),
    )

    print("Starting background rumor polling...")
    async with combined_feeds.stream() as streamer:
        async for source, topic in streamer:
            await rumor_service.record_sighting(topic, source)
            velocity = await rumor_service.get_velocity(topic)
            print(f"Recorded sighting for '{topic}' from '{source}'. Current velocity: {velocity:.2f} mentions/min")
            if velocity > alert_threshold:
                print(f"ALERT! High velocity detected for topic '{topic}': {velocity:.2f} mentions/min")


# Use the client from the cache service to share the connection pool
rumor_service = RumorService(redis_client=cache_service._client)
