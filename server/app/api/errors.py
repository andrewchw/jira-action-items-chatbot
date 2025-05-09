from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from typing import Any, Dict, Optional
import logging

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
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handler for custom API exceptions"""
    error_response = {
        "detail": exc.detail,
        "type": exc.__class__.__name__,
    }
    
    if exc.error_code:
        error_response["code"] = exc.error_code
    
    # Log the error with context
    logger.error(
        f"API Error: {exc.__class__.__name__} - {exc.detail}",
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


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions"""
    error_message = f"Internal server error: {str(exc)}"
    error_response = {
        "detail": error_message,
        "type": exc.__class__.__name__,
    }
    
    # Log the error with context and traceback
    logger.exception(
        f"Unhandled Exception: {str(exc)}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# Function to register error handlers with the FastAPI app
def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI application"""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 