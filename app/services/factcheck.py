import asyncio
import random
from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.exceptions import ExternalAPIError
from app.models.claim import Citation, FactCheckResult


class FactCheckService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._news_api_url = "https://newsapi.org/v2/everything"
        self._google_fc_api_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def _call_api(self, url: str, headers: dict, params: dict) -> httpx.Response:
        try:
            response = await self._client.get(url, headers=headers, params=params)
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

    async def _query_google_fact_check(self, claim_text: str) -> FactCheckResult:
        # This is a mocked implementation
        await asyncio.sleep(random.uniform(0.5, 1.0))

        if "true" in claim_text.lower():
            verdict = "True"
            explanation = "This claim is supported by multiple sources."
        elif "false" in claim_text.lower():
            verdict = "False"
            explanation = "This claim has been debunked by fact-checkers."
        else:
            verdict = "Unverified"
            explanation = "Not enough information to verify this claim."

        citations = [
            Citation(url=f"https://example.com/factcheck/{i}", title=f"Fact Check Report #{i}", source="Example Source")
            for i in range(3)
        ] if verdict != "Unverified" else []

        return FactCheckResult(verdict=verdict, explanation=explanation, citations=citations)

    async def _search_news_api(self, claim_text: str) -> List[Citation]:
        # This is a mocked implementation to supplement the fact check
        await asyncio.sleep(random.uniform(0.8, 1.5))
        return [
            Citation(url=f"https://example.com/news/{i}", title=f"News Article #{i}", source="Example News")
            for i in range(2)
        ]

    async def check_claim(self, claim_text: str) -> FactCheckResult:
        try:
            result = await self._query_google_fact_check(claim_text)
            if result.verdict == "Unverified":
                news_citations = await self._search_news_api(claim_text)
                if news_citations:
                    result.explanation += " However, related news articles were found."
                    # In a real app, you might not add them or handle them differently
                    result.citations.extend(news_citations)
            return result
        except ExternalAPIError as e:
            raise ExternalAPIError(
                service_name="FactCheck",
                detail=f"Failed to get fact check results: {e.message}",
            )


factcheck_service = FactCheckService(client=httpx.AsyncClient(timeout=20.0))
