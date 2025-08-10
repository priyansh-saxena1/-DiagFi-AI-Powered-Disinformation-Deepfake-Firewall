from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class MediaSubmissionRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL of the media to be analyzed.")


class BoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int


class DeepfakeDetectionResult(BaseModel):
    probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of the media being a deepfake."
    )
    bounding_boxes: List[BoundingBox] = Field(
        default_factory=list, description="List of bounding boxes for detected fakes."
    )
