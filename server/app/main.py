import os
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
try:
    import nltk
except ImportError:
    nltk = None
from app.api import auth  # Import the auth module
from app.api import reminders  # Import the reminders module
from app.core.config import settings, get_settings
from app.services.memory import memory_service
from app.services.reminders import reminder_service  # Import the reminder service
from app.models.database import db_manager, create_db_and_tables
from app.api.errors import register_exception_handlers
from app.api.auth import get_oauth_router, revoke_oauth_token_endpoint
from app.services.jira import JiraClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(settings.API_TITLE)

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

# Create FastAPI instance
def get_application() -> FastAPI:
    """
    Initialize and return the FastAPI application.
    """
    application = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
    )
    
    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    register_exception_handlers(application)
    
    # Include routes
    from app.api import endpoints
    
    # Add endpoints router
    application.include_router(
        endpoints.router,
        prefix="/api",
        tags=["chat"],
    )
    
    # Add reminders router
    application.include_router(
        reminders.router,
        prefix="/api/reminders",
        tags=["reminders"],
    )
    
    # Include OAuth router
    application.include_router(get_oauth_router(), prefix="/auth", tags=["auth"])
    application.include_router(revoke_oauth_token_endpoint(), prefix="/auth", tags=["auth"])
    
    # Define startup and shutdown events
    @application.on_event("startup")
    async def startup_event():
        """Initialize application on startup."""
        logger.info("Starting up application...")
        
        # Create database tables
        create_db_and_tables()
        
        # Initialize memory service if available
        try:
            await memory_service.initialize()
            logger.info("Memory service initialized successfully.")
        except Exception as e:
            logger.warning(f"Memory service initialization failed: {str(e)}")
            # If memory service fails, the app can still run with limited functionality
        
        # Start background thread for syncing Jira users
        sync_thread = threading.Thread(target=start_jira_user_sync_scheduler)
        sync_thread.daemon = True
        sync_thread.start()
        
        logger.info("Application startup complete.")

    @application.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        logger.info("Shutting down application...")
        
        # Cleanup memory service if initialized
        try:
            await memory_service.cleanup()
            logger.info("Memory service cleaned up successfully.")
        except Exception as e:
            logger.warning(f"Memory service cleanup failed: {str(e)}")
    
    # Request timing middleware
    @application.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Track and log request processing time."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        # Add header with processing time
        response.headers["X-Process-Time"] = str(process_time)
        # Log request timing
        logger.info(f"Request timing: {request.method} {request.url.path} - {process_time:.4f}s")
        return response
    
    # Return configured application
    return application

# Create application instance
app = get_application()

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

# Function to sync Jira users periodically
def sync_jira_users():
    """
    Sync Jira users to local database.
    """
    try:
        from app.models.database import get_db
        db = next(get_db())
        
        # Create Jira client
        client = JiraClient()
        
        # Sync users
        logger.info("Starting scheduled Jira user sync...")
        result = client.sync_users(db)
        
        if result["success"]:
            logger.info(f"Successfully synced {result['updated_users']} Jira users out of {result['total_users']} total")
        else:
            logger.error(f"Failed to sync Jira users: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in scheduled Jira user sync: {str(e)}", exc_info=True)

# Scheduler for Jira user sync
def start_jira_user_sync_scheduler():
    """
    Start a scheduler to periodically sync Jira users.
    """
    # Initial sync after startup
    sync_jira_users()
    
    sync_interval = int(os.getenv("JIRA_USER_SYNC_INTERVAL", "3600"))  # Default: 1 hour
    
    while True:
        # Sleep until next sync
        time.sleep(sync_interval)
        
        # Perform sync
        sync_jira_users() 