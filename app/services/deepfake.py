import asyncio
import random

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.exceptions import ExternalAPIError
from app.models.media import BoundingBox, DeepfakeDetectionResult


class DeepfakeService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._seam_api_url = "https://api.seam.meta.com/v1/media/analyze"
        self._ms_video_api_url = "https://api.videoauthenticator.microsoft.com/v1/frames"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def _call_api(self, url: str, headers: dict, json_data: dict) -> httpx.Response:
        try:
            response = await self._client.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            raise ExternalAPIError(service_name=url, detail=f"Request timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ExternalAPIError(
                service_name=url,
                status_code=e.response.status_code,
                detail=f"HTTP error: {e.response.text}",
            )

    async def _analyze_with_meta_seam(self, media_url: str) -> DeepfakeDetectionResult:
        # This is a mocked implementation
        await asyncio.sleep(random.uniform(0.5, 1.5))
        if "error" in media_url:
            raise ExternalAPIError("Meta SEAM", detail="Simulated processing failure.")

        prob = random.uniform(0.0, 1.0)
        return DeepfakeDetectionResult(
            probability=prob,
            bounding_boxes=[BoundingBox(x_min=10, y_min=10, x_max=50, y_max=50)] if prob > 0.7 else [],
        )

    async def _analyze_with_ms_video_auth(self, media_url: str) -> DeepfakeDetectionResult:
        # This is a mocked implementation
        await asyncio.sleep(random.uniform(1.0, 2.0))
        if "error" in media_url:
            raise ExternalAPIError("MS Video Auth", detail="Simulated processing failure.")

        prob = random.uniform(0.0, 1.0)
        return DeepfakeDetectionResult(probability=prob, bounding_boxes=[])

    async def analyze_media(self, media_url: str) -> DeepfakeDetectionResult:
        try:
            return await self._analyze_with_meta_seam(media_url)
        except ExternalAPIError:
            try:
                return await self._analyze_with_ms_video_auth(media_url)
            except ExternalAPIError as e:
                raise ExternalAPIError(
                    service_name="DeepfakeDetection",
                    detail=f"All providers failed. Last error: {e.message}",
                )


deepfake_service = DeepfakeService(client=httpx.AsyncClient(timeout=30.0))
