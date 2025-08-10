from typing import List, Literal

from pydantic import BaseModel, Field, HttpUrl


class ClaimSubmissionRequest(BaseModel):
    text: str = Field(..., min_length=10, description="The text of the claim to be checked.")


class Citation(BaseModel):
    url: HttpUrl
    title: str
    source: str


class FactCheckResult(BaseModel):
    verdict: Literal["True", "False", "Unverified"]
    explanation: str
    citations: List[Citation] = Field(
        default_factory=list, description="Top 3 citations supporting the verdict."
    )
