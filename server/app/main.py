from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict
import sys
import os
import subprocess

# Fix path for FastAPI compatibility issues
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app modules after path fix
from app.api import endpoints
from app.core.config import settings, get_settings
from app.services.memory import memory_service

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
    
    # Include API endpoints
    application.include_router(
        endpoints.router,
        prefix="/api",
        tags=["api"],
    )
    
    # Define startup and shutdown events
    @application.on_startup
    async def startup_event():
        """
        Initialize services on startup
        """
        logger.info("Starting application...")
        
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

    @application.on_shutdown
    async def shutdown_event():
        """
        Clean up resources on shutdown
        """
        logger.info("Shutting down application...")
        
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
    port = int(os.environ.get("PORT", settings.PORT))
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port,
        reload=settings.DEBUG
    ) 