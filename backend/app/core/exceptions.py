from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppException(Exception):
    """
    Base domain exception for Smart Library application errors.
    Encapsulates machine-readable error codes and human-readable messages.
    """
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()


class NotFoundException(AppException):
    """Entity or resource was not found."""
    def __init__(self, message: str, code: str = "NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ConflictException(AppException):
    """Business rule, seat allocation collision, or unique constraint violation."""
    def __init__(self, message: str, code: str = "CONFLICT", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class ValidationException(AppException):
    """Business logic validation failure."""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class UnauthorizedException(AppException):
    """Missing or invalid authentication credentials."""
    def __init__(self, message: str = "Authentication credentials required", code: str = "UNAUTHORIZED", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class ForbiddenException(AppException):
    """Insufficient privileges (e.g. staff attempting admin-only operations)."""
    def __init__(self, message: str = "Insufficient permissions", code: str = "FORBIDDEN", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


# Global FastAPI Exception Handlers

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handles domain-specific AppExceptions and formats standard error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": exc.timestamp,
                "path": request.url.path
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Transforms FastAPI / Pydantic validation errors into clean RFC-compliant errors."""
    formatted_errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        formatted_errors.append({
            "field": field_path,
            "message": err.get("msg"),
            "type": err.get("type")
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "REQUEST_VALIDATION_FAILED",
                "message": "Incoming request payload failed schema validation",
                "details": {"validation_errors": formatted_errors},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path
            }
        }
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unexpected exceptions to prevent raw stack traces from leaking to clients."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please contact system support.",
                "details": {"error_type": type(exc).__name__},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path
            }
        }
    )
