from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict
import sys
import os
import subprocess
import time
from starlette.middleware.base import BaseHTTPMiddleware
import json
from datetime import datetime
import asyncio
import nltk
from pathlib import Path

# Fix path for FastAPI compatibility issues
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app modules after path fix
from app.api import endpoints
from app.api import auth  # Import the auth module
from app.api import reminders  # Import the reminders module
from app.core.config import settings, get_settings
from app.services.memory import memory_service
from app.services.reminders import reminder_service  # Import the reminder service
from app.models.database import db_manager
from app.api.errors import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Make sure NLTK data is downloaded during startup
try:
    # Create NLTK data directory if it doesn't exist
    nltk_data_dir = Path.home() / 'nltk_data'
    nltk_data_dir.mkdir(exist_ok=True)
    
    # Download required NLTK data
    logger.info("Checking for required NLTK data...")
    for resource in ['punkt', 'averaged_perceptron_tagger']:
        try:
            if resource == 'punkt':
                nltk.data.find('tokenizers/punkt')
            else:
                nltk.data.find(f'taggers/{resource}')
        except LookupError:
            logger.info(f"Downloading NLTK resource: {resource}")
            nltk.download(resource, quiet=True)
            logger.info(f"Successfully downloaded {resource}")
except Exception as e:
    logger.error(f"Error setting up NLTK data: {str(e)}")
    logger.info("Application will continue with fallback tokenization")

# Add request timing middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log timing information for non-static requests
        if not request.url.path.startswith(("/static/", "/favicon.ico")):
            logger.info(
                f"Request timing: {request.method} {request.url.path} - {process_time:.4f}s",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "client_host": request.client.host if request.client else None
                }
            )
        
        return response

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    application = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request timing middleware
    application.add_middleware(TimingMiddleware)
    
    # Register exception handlers
    register_exception_handlers(application)
    
    # Include API endpoints
    application.include_router(
        endpoints.router,
        prefix="/api",
        tags=["api"],
    )
    
    # Include authentication endpoints
    application.include_router(
        auth.router,
        prefix="/api/auth",
        tags=["auth"],
    )
    
    # Include reminder endpoints
    application.include_router(
        reminders.router,
        prefix="/api/reminders",
        tags=["reminders"],
    )
    
    # Define startup and shutdown events
    @application.on_event("startup")
    async def startup_event():
        """
        Initialize services on startup
        """
        logger.info("Starting application...")
        
        # Initialize database
        try:
            logger.info("Initializing database...")
            # Database is initialized when the db_manager is imported
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            logger.warning("Starting with limited database functionality")
        
        # Start reminder service
        try:
            logger.info("Starting reminder service...")
            await reminder_service.start()
            logger.info("Reminder service started successfully")
        except Exception as e:
            logger.error(f"Failed to start reminder service: {e}")
            logger.warning("Starting with limited reminder functionality")
        
        # Fall back to alternative memory implementation if MCP server is not available
        try:
            # Try to start memory service
            logger.info("Trying to connect to or start memory service...")
            await memory_service.start()
            
            # Log success
            memory_status = memory_service.use_fallback
            if memory_status:
                logger.info("Using fallback in-memory graph implementation")
            else:
                logger.info("Connected to MCP knowledge graph server successfully")
            
        except Exception as e:
            logger.error(f"Failed to start memory service: {e}")
            logger.warning("Starting with limited functionality (memory service unavailable)")
            # If memory service fails, the app can still run with limited functionality

    @application.on_event("shutdown")
    async def shutdown_event():
        """
        Clean up resources on shutdown
        """
        logger.info("Shutting down application...")
        
        # Stop reminder service
        try:
            await reminder_service.stop()
            logger.info("Reminder service stopped")
        except Exception as e:
            logger.error(f"Error stopping reminder service: {e}")
        
        # Stop memory service if it was started
        try:
            await memory_service.stop()
            logger.info("Memory service stopped")
        except Exception as e:
            logger.error(f"Error stopping memory service: {e}")

    # For standalone usage, start a separate memory process if running directly
    if __name__ == "__main__":
        # Check if memory server is already running
        try:
            # If not using fallback already, check if we can start a memory server
            if not os.environ.get("USE_FALLBACK_MEMORY", "False").lower() == "true":
                # Look for an external memory server implementation
                memory_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                           "simple_api", "memory_api.py")
                if os.path.exists(memory_script):
                    logger.info(f"Found standalone memory server script at: {memory_script}")
                    # Start the memory server in a separate process
                    subprocess.Popen(
                        [sys.executable, memory_script, "8001", "memory.jsonl"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    logger.info("Started standalone memory server on port 8001")
                    os.environ["MEMORY_URL"] = "http://localhost:8001"
                else:
                    logger.warning("No standalone memory server script found. Using fallback implementation.")
                    os.environ["USE_FALLBACK_MEMORY"] = "True"
        except Exception as e:
            logger.error(f"Failed to start standalone memory server: {e}")
            logger.warning("Using fallback memory implementation")
            os.environ["USE_FALLBACK_MEMORY"] = "True"

    return application

app = create_application()

# Check if script is run directly, not through an import
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", settings.API_PORT))
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port,
        reload=settings.DEBUG
    ) 