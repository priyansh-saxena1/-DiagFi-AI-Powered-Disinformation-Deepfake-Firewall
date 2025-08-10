from app.exceptions import ServiceError
from app.mcp import tool
from app.models.claim import ClaimSubmissionRequest, FactCheckResult
from app.services.cache import cache_service
from app.services.factcheck import factcheck_service
from app.utils.hashing import generate_hash


@tool
async def check_text_claim(submission: ClaimSubmissionRequest) -> FactCheckResult:
    """
    Checks a textual claim against fact-checking databases.

    This tool checks a cache first. If the result for the given claim
    is not cached, it uses the fact-checking service to verify it.
    """
    cache_key = f"text_claim:{generate_hash(submission.model_dump())}"
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return FactCheckResult(**cached_result)

    try:
        result = await factcheck_service.check_claim(submission.text)
    except ServiceError as e:
        raise e

    await cache_service.set(cache_key, result.model_dump(), expire=7200)  # Cache for 2 hours
    return result
