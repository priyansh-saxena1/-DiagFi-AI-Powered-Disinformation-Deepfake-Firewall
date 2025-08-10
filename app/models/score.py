from pydantic import BaseModel, Field, HttpUrl


class VeracityScoreRequest(BaseModel):
    media_fake_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of media being fake (from detect_media_fake)."
    )
    claim_verdict: str = Field(
        ...,
        description="Verdict from check_text_claim ('True', 'False', or 'Unverified')."
    )
    source_url: HttpUrl = Field(
        ..., description="The URL of the source of the claim/media."
    )


class VeracityScoreResult(BaseModel):
    score: int = Field(..., ge=0, le=100, description="The final veracity score, from 0 (low) to 100 (high).")
    explanation: str = Field(..., description="An explanation of how the score was calculated.")
