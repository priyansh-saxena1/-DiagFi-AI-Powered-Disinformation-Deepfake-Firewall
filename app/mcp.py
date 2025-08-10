from functools import wraps
from typing import Any, Callable, Coroutine


def tool(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    A decorator to mark a function as an MCP tool.

    In a real scenario, this would register the function with the MCP framework.
    For this project, it simply marks the function for discovery by FastAPI.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await func(*args, **kwargs)

    setattr(wrapper, "_is_mcp_tool", True)
    return wrapper
