from app.exceptions import ServiceError
from app.mcp import tool
from app.models.media import DeepfakeDetectionResult, MediaSubmissionRequest
from app.services.cache import cache_service
from app.services.deepfake import deepfake_service
from app.utils.hashing import generate_hash


@tool
async def detect_media_fake(
    submission: MediaSubmissionRequest,
) -> DeepfakeDetectionResult:
    """
    Analyzes a media URL for signs of deepfake manipulation.

    This tool checks a cache first. If the result for the given URL
    is not cached, it uses the deepfake detection service to analyze it.
    """
    cache_key = f"media_fake:{generate_hash(submission.model_dump())}"
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return DeepfakeDetectionResult(**cached_result)

    try:
        result = await deepfake_service.analyze_media(str(submission.url))
    except ServiceError as e:
        # In a real app, you might want to re-raise a more user-friendly error
        # or return a specific error model. For now, we propagate the service error.
        raise e

    await cache_service.set(cache_key, result.model_dump(), expire=7200)  # Cache for 2 hours
    return result
