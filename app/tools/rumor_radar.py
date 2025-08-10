from app.mcp import tool
from app.models.rumor import RumorRadarRequest, RumorRadarResult
from app.services.rumor import rumor_service


@tool
async def check_rumor_velocity(request: RumorRadarRequest) -> RumorRadarResult:
    """
    Checks the current velocity of a given rumor topic.
    Velocity is measured in mentions per minute over a specified time window.
    """
    velocity = await rumor_service.get_velocity(
        topic=request.topic, window_seconds=request.window_seconds
    )
    return RumorRadarResult(
        topic=request.topic,
        velocity=velocity,
        window_seconds=request.window_seconds,
    )
