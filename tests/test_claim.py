import tenacity
from unittest.mock import AsyncMock

import httpx
import pytest

from app.exceptions import ExternalAPIError
from app.models.claim import Citation, FactCheckResult
from app.services.factcheck import FactCheckService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_http_client() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def factcheck_service(mock_http_client: AsyncMock) -> FactCheckService:
    # We are testing the service, so we mock the client it uses.
    # The service instance is created with the mocked client.
    service = FactCheckService(client=mock_http_client)
    return service


async def test_check_claim_true_verdict(factcheck_service: FactCheckService, mocker):
    """Test a claim that returns a 'True' verdict from the primary fact-checker."""
    claim_text = "this statement is true"
    expected_result = FactCheckResult(
        verdict="True",
        explanation="Supported by sources.",
        citations=[Citation(url="https://example.com/1", title="Report 1", source="Source 1")],
    )

    mock_google_fc = mocker.patch.object(
        factcheck_service, "_query_google_fact_check", return_value=expected_result
    )
    mock_news_api = mocker.patch.object(factcheck_service, "_search_news_api")

    result = await factcheck_service.check_claim(claim_text)

    assert result == expected_result
    mock_google_fc.assert_awaited_once_with(claim_text)
    mock_news_api.assert_not_awaited()


async def test_check_claim_unverified_with_news_fallback(
    factcheck_service: FactCheckService, mocker
):
    """Test a claim that is 'Unverified' and falls back to NewsAPI."""
    claim_text = "this statement is unverified"
    unverified_result = FactCheckResult(verdict="Unverified", explanation="Not enough info.", citations=[])
    news_citations = [Citation(url="https://example.com/news", title="News", source="News Source")]

    mock_google_fc = mocker.patch.object(
        factcheck_service, "_query_google_fact_check", return_value=unverified_result
    )
    mock_news_api = mocker.patch.object(
        factcheck_service, "_search_news_api", return_value=news_citations
    )

    result = await factcheck_service.check_claim(claim_text)

    mock_google_fc.assert_awaited_once_with(claim_text)
    mock_news_api.assert_awaited_once_with(claim_text)
    assert result.verdict == "Unverified"
    assert "related news articles" in result.explanation
    assert len(result.citations) == 1


async def test_check_claim_api_error(factcheck_service: FactCheckService, mocker):
    """Test that an API error from the service is propagated."""
    claim_text = "this will fail"
    mocker.patch.object(
        factcheck_service,
        "_query_google_fact_check",
        side_effect=ExternalAPIError("Google Fact Check"),
    )

    with pytest.raises(ExternalAPIError) as exc_info:
        await factcheck_service.check_claim(claim_text)

    assert "Failed to get fact check results" in exc_info.value.message


async def test_call_api_handles_timeout(
    factcheck_service: FactCheckService, mock_http_client: AsyncMock
):
    """Test that the _call_api wrapper correctly handles TimeoutException."""
    mock_http_client.get.side_effect = httpx.TimeoutException(
        "Timeout", request=AsyncMock()
    )

    with pytest.raises(tenacity.RetryError) as exc_info:
        await factcheck_service._call_api("http://fakeurl", {}, {})

    final_exception = exc_info.value.last_attempt.exception()
    assert isinstance(final_exception, ExternalAPIError)
    assert "Request timed out" in final_exception.message
