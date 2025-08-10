import asyncio
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.exceptions import ServiceError
from app.services.cache import cache_service
from app.services.rumor import poll_feeds_background_task, rumor_service
from app.tools.check_text_claim import check_text_claim
from app.tools.detect_media_fake import detect_media_fake
from app.tools.educate_user import play_quiz
from app.tools.rumor_radar import check_rumor_velocity
from app.tools.veracity_score import calculate_veracity_score


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    print("Starting background services...")
    background_task = asyncio.create_task(poll_feeds_background_task(rumor_service))
    yield
    print("Shutting down background services...")
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        print("Rumor polling task successfully cancelled.")
    await cache_service.close()


app = FastAPI(
    title="DiagFi - AI-Powered Disinformation & Deepfake Firewall",
    description="MCP Server for the #BuildWithPuch Hackathon.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(status_code=503, content={"detail": exc.message})


# --- MCP Tool Registration ---

class McpToolInfo(BaseModel):
    name: str
    description: str
    endpoint: str

TOOLS: List[McpToolInfo] = [
    McpToolInfo(
        name="detect_media_fake",
        description=detect_media_fake.__doc__,
        endpoint="/tools/detect-media-fake",
    ),
    McpToolInfo(
        name="check_text_claim",
        description=check_text_claim.__doc__,
        endpoint="/tools/check-text-claim",
    ),
    McpToolInfo(
        name="calculate_veracity_score",
        description=calculate_veracity_score.__doc__,
        endpoint="/tools/calculate-veracity-score",
    ),
    McpToolInfo(
        name="check_rumor_velocity",
        description=check_rumor_velocity.__doc__,
        endpoint="/tools/check-rumor-velocity",
    ),
    McpToolInfo(
        name="play_quiz",
        description=play_quiz.__doc__,
        endpoint="/tools/play-quiz",
    ),
]

@app.get("/mcp", response_model=List[McpToolInfo], tags=["MCP"])
async def mcp_manifest():
    """Provides a manifest of available MCP tools."""
    return TOOLS


# --- API Router ---

api_router = APIRouter(prefix="/tools")

# A helper to reduce boilerplate
def add_tool_endpoint(path: str, func: Callable[..., Any]):
    api_router.add_api_route(
        path,
        func,
        methods=["POST"],
        tags=["MCP Tools"],
        response_model=func.__annotations__["return"],
    )

add_tool_endpoint("/detect-media-fake", detect_media_fake)
add_tool_endpoint("/check-text-claim", check_text_claim)
add_tool_endpoint("/calculate-veracity-score", calculate_veracity_score)
add_tool_endpoint("/check-rumor-velocity", check_rumor_velocity)
add_tool_endpoint("/play-quiz", play_quiz)

app.include_router(api_router)


@app.get("/", tags=["Health Check"])
async def health_check():
    """A simple health check endpoint."""
    return {"status": "ok"}
