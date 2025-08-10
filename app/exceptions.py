class ServiceError(Exception):
    """Base exception for service layer errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExternalAPIError(ServiceError):
    """Raised when an external API call fails."""

    def __init__(self, service_name: str, status_code: int | None = None, detail: str | None = None):
        self.service_name = service_name
        self.status_code = status_code
        self.detail = detail
        message = f"Error from {service_name}"
        if status_code:
            message += f" (Status: {status_code})"
        if detail:
            message += f": {detail}"
        super().__init__(message)


class CacheError(ServiceError):
    """Raised for cache-related errors."""


class ResourceNotFoundError(ServiceError):
    """Raised when a resource is not found."""
