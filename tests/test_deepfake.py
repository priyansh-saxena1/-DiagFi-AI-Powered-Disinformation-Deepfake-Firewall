from unittest.mock import AsyncMock

import httpx
import pytest

from app.exceptions import ExternalAPIError
from app.models.media import DeepfakeDetectionResult
from app.services.deepfake import DeepfakeService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_client() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def deepfake_service(mock_client: AsyncMock) -> DeepfakeService:
    return DeepfakeService(client=mock_client)


async def test_analyze_media_primary_success(
    deepfake_service: DeepfakeService, mock_client: AsyncMock, mocker
):
    """Test successful analysis by mocking the HTTP client response."""
    media_url = "https://example.com/video.mp4"

    # Mock the _call_api method to avoid actual HTTP calls but test the parsing logic
    mocker.patch.object(deepfake_service, "_analyze_with_ms_video_auth") # Not used
    mock_seam = mocker.patch.object(
        deepfake_service, "_analyze_with_meta_seam",
        return_value=DeepfakeDetectionResult(probability=0.9, bounding_boxes=[])
    )

    result = await deepfake_service.analyze_media(media_url)

    assert result.probability == 0.9
    mock_seam.assert_awaited_once_with(media_url)


async def test_analyze_media_fallback_success(
    deepfake_service: DeepfakeService, mock_client: AsyncMock, mocker
):
    """Test fallback by making the primary service mock raise an error."""
    media_url = "https://example.com/video.mp4"

    mocker.patch.object(
        deepfake_service, "_analyze_with_meta_seam",
        side_effect=ExternalAPIError("Meta SEAM", detail="Simulated failure")
    )
    mock_ms = mocker.patch.object(
        deepfake_service, "_analyze_with_ms_video_auth",
        return_value=DeepfakeDetectionResult(probability=0.8, bounding_boxes=[])
    )

    result = await deepfake_service.analyze_media(media_url)

    assert result.probability == 0.8
    mock_ms.assert_awaited_once_with(media_url)


async def test_analyze_media_all_fail(
    deepfake_service: DeepfakeService, mock_client: AsyncMock, mocker
):
    """Test failure when all providers fail."""
    media_url = "https://example.com/video.mp4"

    mocker.patch.object(
        deepfake_service, "_analyze_with_meta_seam",
        side_effect=ExternalAPIError("Meta SEAM", detail="Simulated failure")
    )
    mocker.patch.object(
        deepfake_service, "_analyze_with_ms_video_auth",
        side_effect=ExternalAPIError("MS Video Auth", detail="Simulated failure")
    )

    with pytest.raises(ExternalAPIError) as exc_info:
        await deepfake_service.analyze_media(media_url)

    assert "All providers failed" in exc_info.value.message


import tenacity


async def test_call_api_handles_http_error(
    deepfake_service: DeepfakeService, mock_client: AsyncMock
):
    """Test that the _call_api wrapper correctly handles HTTPStatusError."""
    mock_client.post.side_effect = httpx.HTTPStatusError(
        "Not Found", request=AsyncMock(), response=AsyncMock(status_code=404, text="Not Found")
    )

    with pytest.raises(tenacity.RetryError) as exc_info:
        await deepfake_service._call_api("http://fakeurl", {}, {})

    # Check that the final exception wrapped by tenacity is our custom one
    final_exception = exc_info.value.last_attempt.exception()
    assert isinstance(final_exception, ExternalAPIError)
    assert final_exception.status_code == 404
    assert "HTTP error" in final_exception.message
