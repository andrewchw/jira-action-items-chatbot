import asyncio
import logging
import os
import json
import sys
import traceback
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ensure we can import from the app directory
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.services.memory import memory_service, MemoryService, MCP_EXECUTABLE
    from app.core.config import settings
    logger.info("Successfully imported modules")
    logger.info(f"Using MCP executable: {MCP_EXECUTABLE}")
except Exception as e:
    logger.error(f"Failed to import modules: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)

async def test_external_connection():
    """Test connecting to an external MCP server"""
    logger.info("Testing external MCP connection...")
    
    # First try subprocess command to check if mcp-knowledge-graph is available
    try:
        logger.info(f"Testing MCP CLI availability using: {MCP_EXECUTABLE}")
        process = await asyncio.create_subprocess_exec(
            MCP_EXECUTABLE, "--help",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info("MCP CLI is available")
            logger.info(f"MCP CLI output: {stdout.decode()[:100]}...")
        else:
            logger.error(f"MCP CLI error: {stderr.decode()}")
            logger.error(f"MCP CLI not available at {MCP_EXECUTABLE}, check path")
            return False
    except Exception as e:
        logger.error(f"Error checking MCP CLI: {str(e)}")
        logger.error(traceback.format_exc())
        logger.error(f"MCP CLI not available at {MCP_EXECUTABLE}, check path")
        return False
    
    # Now test memory service connect method
    try:
        memory_path = Path(settings.MEMORY_PATH).resolve()
        logger.info(f"Using memory path: {memory_path}")
        
        # Make sure memory file exists and is absolute
        logger.info(f"Resolved memory path: {memory_path}")
        
        if not memory_path.exists():
            logger.info(f"Memory file {memory_path} does not exist, creating empty file")
            os.makedirs(memory_path.parent, exist_ok=True)
            with open(memory_path, 'w') as f:
                f.write("[]")
        
        # Test connection
        logger.info("Creating memory service instance")
        service = MemoryService(str(memory_path))
        logger.info("Calling connect method")
        result = await service.connect()
        
        if result:
            logger.info("Successfully connected to MCP server")
            return True
        else:
            logger.error("Failed to connect to MCP server")
            return False
    except Exception as e:
        logger.error(f"Error testing MCP connection: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def test_create_entity():
    """Test creating an entity in the memory graph"""
    try:
        logger.info("Testing entity creation...")
        result = await memory_service.create_entities([
            {
                "name": "test_entity",
                "entityType": "test",
                "observations": ["This is a test entity created at " + 
                                 str(asyncio.get_event_loop().time())]
            }
        ])
        
        logger.info(f"Entity creation result: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        logger.error(f"Error creating entity: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def test_read_graph():
    """Test reading the memory graph"""
    try:
        logger.info("Testing reading graph...")
        result = await memory_service.read_graph()
        
        if result:
            logger.info(f"Found {len(result.get('entities', []))} entities in graph")
            logger.info(f"Graph result: {json.dumps(result, indent=2)}")
            return True
        else:
            logger.error("Empty result from read_graph")
            return False
    except Exception as e:
        logger.error(f"Error reading graph: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run all tests"""
    logger.info("Starting memory service tests")
    
    # Test connection to MCP server
    connection_result = await test_external_connection()
    if connection_result:
        logger.info("External MCP connection successful")
        
        # Test entity creation
        entity_result = await test_create_entity()
        if entity_result:
            logger.info("Entity creation successful")
        else:
            logger.error("Entity creation failed")
        
        # Test reading graph
        read_result = await test_read_graph()
        if read_result:
            logger.info("Reading graph successful")
        else:
            logger.error("Reading graph failed")
    else:
        logger.error("External MCP connection failed")
    
    logger.info("Memory service tests completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc()) 