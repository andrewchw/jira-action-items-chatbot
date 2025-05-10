from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from typing import Any, Dict, Optional
import logging
import traceback
import json
import requests

logger = logging.getLogger(__name__)

# Custom exception classes
class APIError(Exception):
    """Base class for API exceptions"""
    def __init__(
        self, 
        detail: str, 
        status_code: int = 500, 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.headers = headers


class JiraError(APIError):
    """Exception for Jira API errors"""
    def __init__(
        self, 
        detail: str, 
        status_code: int = 500, 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(detail, status_code, error_code or "JIRA_ERROR", headers)


class LLMError(APIError):
    """Exception for LLM API errors"""
    def __init__(
        self, 
        detail: str, 
        status_code: int = 500, 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(detail, status_code, error_code or "LLM_ERROR", headers)


class DatabaseError(APIError):
    """Exception for database errors"""
    def __init__(
        self, 
        detail: str, 
        status_code: int = 500, 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(detail, status_code, error_code or "DB_ERROR", headers)


class AuthError(APIError):
    """Exception for authentication and authorization errors"""
    def __init__(
        self, 
        detail: str, 
        status_code: int = 401, 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(detail, status_code, error_code or "AUTH_ERROR", headers)


class ValidationError(APIError):
    """Exception for data validation errors"""
    def __init__(
        self, 
        detail: str, 
        status_code: int = 422, 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(detail, status_code, error_code or "VALIDATION_ERROR", headers)


# Exception handlers
async def log_exception(request: Request, exc: Exception) -> None:
    """
    Log exception details including request information
    """
    # Get request details
    method = request.method
    url = str(request.url)
    
    # Get client information
    client_host = request.client.host if request.client else "unknown"
    
    # Format traceback
    tb = traceback.format_exc()
    
    # Log the error with all available context
    logger.error(
        f"Exception during {method} {url} from {client_host}: {str(exc)}\n{tb}",
        extra={
            "method": method,
            "url": url,
            "client_host": client_host,
            "exception_type": type(exc).__name__,
            "exception_detail": str(exc),
        }
    )

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handle API errors with custom status code and detail
    """
    await log_exception(request, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for FastAPI's HTTPException"""
    error_response = {
        "detail": exc.detail,
        "type": "HTTPException",
    }
    
    # Log the error with context
    logger.error(
        f"HTTP Exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=exc.headers
    )


async def requests_exception_handler(request: Request, exc: requests.RequestException) -> JSONResponse:
    """
    Handle exceptions from the requests library (used in OAuth flows)
    """
    await log_exception(request, exc)
    
    # Try to extract response info if available
    status_code = getattr(exc.response, 'status_code', 500) if hasattr(exc, 'response') else 500
    
    # Try to get response content
    try:
        if hasattr(exc, 'response') and exc.response is not None:
            content = exc.response.json()
            detail = f"External API error: {json.dumps(content)}"
        else:
            detail = f"External API error: {str(exc)}"
    except (ValueError, AttributeError):
        if hasattr(exc, 'response') and exc.response is not None:
            detail = f"External API error: {exc.response.text}"
        else:
            detail = f"External API error: {str(exc)}"
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail}
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle validation errors
    """
    await log_exception(request, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Generic handler for all unhandled exceptions
    """
    await log_exception(request, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


# Function to register error handlers with the FastAPI app
def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI application"""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(requests.RequestException, requests_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered successfully") 