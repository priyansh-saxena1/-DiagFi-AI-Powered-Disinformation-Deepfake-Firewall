import re

from app.mcp import tool
from app.models.score import VeracityScoreRequest, VeracityScoreResult


def _get_claim_false_probability(verdict: str) -> float:
    """Converts a verdict string to a probability of being false."""
    return {"True": 0.0, "False": 1.0, "Unverified": 0.5}.get(verdict, 0.5)


def _get_source_reputation(source_url: str) -> float:
    """
    A mock function to determine source reputation.
    In a real system, this would use a database like NewsGuard or a custom model.
    """
    hostname = re.sub(r"^www\.", "", source_url.split("/")[2])
    reputable_sources = {"apnews.com", "reuters.com", "bbc.com"}
    questionable_sources = {"infowars.com", "dailycaller.com"}

    if hostname in reputable_sources:
        return 0.9  # High reputation -> low probability of being disinformation
    if hostname in questionable_sources:
        return 0.2  # Low reputation -> high probability of being disinformation
    return 0.6  # Neutral for unknown sources


@tool
async def calculate_veracity_score(request: VeracityScoreRequest) -> VeracityScoreResult:
    """
    Calculates a weighted veracity score based on media, claim, and source analysis.
    The final score represents the likelihood that the information is TRUE.
    """
    media_fake_prob = request.media_fake_probability
    claim_false_prob = _get_claim_false_probability(request.claim_verdict)

    # Source reputation here is from 0-1, where 1 is most reputable.
    # We need to convert it to a "disinformation probability".
    source_reputation = _get_source_reputation(str(request.source_url))
    source_disinfo_prob = 1.0 - source_reputation

    # Calculate the weighted probability of the content being FAKE
    fake_score = (
        0.4 * media_fake_prob
        + 0.3 * claim_false_prob
        + 0.3 * source_disinfo_prob
    )

    # Veracity score is the inverse (1 - fake_score), scaled to 100
    veracity_score = int((1.0 - fake_score) * 100)

    explanation = (
        f"Score calculated based on: "
        f"Media Fake Prob ({media_fake_prob:.2f}), "
        f"Claim False Prob ({claim_false_prob:.2f}), "
        f"Source Disinfo Prob ({source_disinfo_prob:.2f})."
    )

    return VeracityScoreResult(score=veracity_score, explanation=explanation)
