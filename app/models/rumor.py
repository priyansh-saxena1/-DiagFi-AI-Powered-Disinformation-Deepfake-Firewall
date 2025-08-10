from pydantic import BaseModel, Field


class RumorRadarRequest(BaseModel):
    topic: str = Field(..., description="The topic to check for rumor velocity (e.g., 'election-fraud').")
    window_seconds: int = Field(
        default=60, gt=0, le=3600, description="The time window in seconds to calculate velocity."
    )


class RumorRadarResult(BaseModel):
    topic: str
    velocity: float = Field(..., description="The velocity of the rumor in mentions per minute.")
    window_seconds: int
