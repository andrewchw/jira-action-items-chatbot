import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# Path to the MCP Knowledge Graph executable
MCP_EXECUTABLE = os.environ.get(
    "MCP_KNOWLEDGE_GRAPH_PATH", 
    r"C:\Users\Loupor\AppData\Roaming\npm\mcp-knowledge-graph.cmd"
)

class SimpleInMemoryGraph:
    """Simple in-memory implementation for demonstration purposes when MCP server isn't available"""
    
    def __init__(self, memory_path: Optional[str] = None):
        self.memory_path = memory_path
        self.entities = []
        self.relations = []
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from file if it exists"""
        try:
            memory_file = Path(self.memory_path).resolve()
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, list):
                            self.entities = data
                        else:
                            logger.warning(f"Memory file {self.memory_path} has invalid format")
            else:
                # Create empty memory file
                os.makedirs(memory_file.parent, exist_ok=True)
                with open(memory_file, 'w') as f:
                    f.write("[]")
                logger.info(f"Created empty memory file {self.memory_path}")
        except Exception as e:
            logger.error(f"Error loading memory: {str(e)}")
    
    def _save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_path, 'w') as f:
                json.dump(self.entities, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")
    
    def create_entities(self, entities):
        """Create multiple new entities in the knowledge graph."""
        for entity in entities:
            # Check if entity already exists
            exists = False
            for existing in self.entities:
                if existing.get("name") == entity.get("name"):
                    exists = True
                    break
            
            if not exists:
                self.entities.append(entity)
        
        self._save_memory()
        return {"success": True, "message": f"Created {len(entities)} entities", "entities": entities}
    
    def create_relations(self, relations):
        """Create multiple new relations between entities."""
        for relation in relations:
            # Check if relation already exists
            exists = False
            for existing in self.relations:
                if (existing.get("from") == relation.get("from") and 
                    existing.get("to") == relation.get("to") and
                    existing.get("relationType") == relation.get("relationType")):
                    exists = True
                    break
            
            if not exists:
                self.relations.append(relation)
        
        return {"success": True, "message": f"Created {len(relations)} relations", "relations": relations}
    
    def add_observations(self, observations):
        """Add new observations to existing entities."""
        for observation in observations:
            entity_name = observation.get("entityName")
            contents = observation.get("contents", [])
            
            for entity in self.entities:
                if entity.get("name") == entity_name:
                    if "observations" not in entity:
                        entity["observations"] = []
                    
                    entity["observations"].extend(contents)
        
        self._save_memory()
        return {"success": True, "message": f"Added observations to entities", "observations": observations}
    
    def read_graph(self):
        """Read the entire knowledge graph."""
        return {
            "entities": self.entities,
            "relations": self.relations
        }
    
    def search_nodes(self, query):
        """Search for nodes based on a query."""
        results = []
        for entity in self.entities:
            if query.lower() in entity.get("name", "").lower():
                results.append(entity)
                continue
                
            for obs in entity.get("observations", []):
                if query.lower() in obs.lower():
                    results.append(entity)
                    break
        
        return {"entities": results}
    
    def open_nodes(self, names):
        """Open specific nodes by name."""
        results = []
        for entity in self.entities:
            if entity.get("name") in names:
                results.append(entity)
        
        return {"entities": results}
    
    def delete_entities(self, entity_names):
        """Delete multiple entities and their relations."""
        initial_count = len(self.entities)
        self.entities = [e for e in self.entities if e.get("name") not in entity_names]
        
        # Also remove related relations
        self.relations = [r for r in self.relations 
                          if r.get("from") not in entity_names and r.get("to") not in entity_names]
        
        self._save_memory()
        return {"success": True, "message": f"Deleted {initial_count - len(self.entities)} entities"}
    
    def delete_observations(self, deletions):
        """Delete specific observations from entities."""
        for deletion in deletions:
            entity_name = deletion.get("entityName")
            observations_to_delete = deletion.get("observations", [])
            
            for entity in self.entities:
                if entity.get("name") == entity_name and "observations" in entity:
                    entity["observations"] = [
                        obs for obs in entity["observations"] 
                        if obs not in observations_to_delete
                    ]
        
        self._save_memory()
        return {"success": True, "message": f"Deleted observations from entities"}
    
    def delete_relations(self, relations):
        """Delete relations from the knowledge graph."""
        initial_count = len(self.relations)
        for relation in relations:
            self.relations = [
                r for r in self.relations 
                if not (r.get("from") == relation.get("from") and 
                        r.get("to") == relation.get("to") and
                        r.get("relationType") == relation.get("relationType"))
            ]
        
        return {"success": True, "message": f"Deleted {initial_count - len(self.relations)} relations"}

class MemoryService:
    """
    Service for interacting with the mcp-knowledge-graph server for persistent memory.
    """
    def __init__(self, memory_path: Optional[str] = None):
        """
        Initialize the memory service.
        
        Args:
            memory_path: Optional path to the memory file. If not provided,
                         it will use the path from settings.
        """
        self.memory_path = memory_path or settings.MEMORY_PATH
        self.mcp_process = None
        self.use_external_server = True  # Default to using external server
        self.fallback_memory = SimpleInMemoryGraph(self.memory_path)
        self.use_fallback = False
        
    async def connect(self):
        """
        Attempt to connect to an already running mcp-knowledge-graph server.
        """
        try:
            # Try to execute a simple command to test the connection
            result = await self.call_function("read_graph", {"random_string": "dummy"})
            logger.info("Successfully connected to existing MCP server")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to existing MCP server: {str(e)}")
            logger.info("Using fallback in-memory implementation")
            self.use_fallback = True
            return False
    
    async def start(self):
        """
        Start or connect to the mcp-knowledge-graph server process.
        First tries to connect to an existing server, then starts a new one if needed.
        """
        # First try to connect to an existing server
        if self.use_external_server:
            logger.info("Attempting to connect to existing MCP server...")
            connected = await self.connect()
            if connected:
                return True
        
        # If connection failed, use fallback
        if not connected:
            logger.warning("Could not connect to MCP server, using fallback implementation")
            self.use_fallback = True
            return True
                
        # If connection failed or use_external_server is False, start a new server
        try:
            logger.info("Starting new MCP server...")
            # Using the explicit path to mcp-knowledge-graph
            cmd = [MCP_EXECUTABLE, "--memory-path", self.memory_path]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            # Make sure memory file exists
            memory_file = Path(self.memory_path).resolve()
            os.makedirs(memory_file.parent, exist_ok=True)
            if not memory_file.exists():
                with open(memory_file, 'w') as f:
                    f.write("[]")
            
            # Start the process
            self.mcp_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            logger.info(f"Started mcp-knowledge-graph server with memory path: {self.memory_path}")
            
            # Read the initial output to confirm the server started
            line = await self.mcp_process.stdout.readline()
            logger.info(f"MCP server startup: {line.decode().strip()}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to start mcp-knowledge-graph server: {str(e)}")
            logger.warning("Using fallback in-memory implementation")
            self.use_fallback = True
            return True
    
    async def stop(self):
        """
        Stop the mcp-knowledge-graph server process if it was started by this service.
        """
        if self.mcp_process:
            try:
                self.mcp_process.terminate()
                await self.mcp_process.wait()
                logger.info("Stopped mcp-knowledge-graph server")
            except Exception as e:
                logger.error(f"Error stopping mcp-knowledge-graph server: {str(e)}")
            finally:
                self.mcp_process = None
    
    async def call_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a function on the mcp-knowledge-graph server.
        
        Args:
            function_name: The name of the function to call
            arguments: The arguments to pass to the function
            
        Returns:
            The result of the function call
        """
        # Use fallback implementation if needed
        if self.use_fallback:
            try:
                logger.info(f"Using fallback for {function_name}")
                if hasattr(self.fallback_memory, function_name):
                    func = getattr(self.fallback_memory, function_name)
                    if function_name == "read_graph":
                        return func()
                    elif function_name == "search_nodes":
                        return func(arguments.get("query", ""))
                    elif function_name == "open_nodes":
                        return func(arguments.get("names", []))
                    else:
                        if "entities" in arguments:
                            return func(arguments["entities"])
                        elif "relations" in arguments:
                            return func(arguments["relations"])
                        elif "observations" in arguments:
                            return func(arguments["observations"])
                        elif "entityNames" in arguments:
                            return func(arguments["entityNames"])
                        elif "deletions" in arguments:
                            return func(arguments["deletions"])
                        else:
                            return {"error": f"Invalid arguments for {function_name}"}
                else:
                    return {"error": f"Function {function_name} not implemented in fallback"}
            except Exception as e:
                logger.error(f"Error in fallback implementation: {str(e)}")
                return {"error": str(e)}
                
        if not self.mcp_process and not self.use_external_server:
            await self.start()
            
        try:
            # Prepare the function call message
            function_call = {
                "name": function_name,
                "arguments": arguments
            }
            
            # Execute locally using CLI if connecting to external server
            if self.use_external_server and not self.mcp_process:
                # Create a temporary input file
                input_file = f"temp_mcp_input_{function_name}.json"
                with open(input_file, 'w') as f:
                    json.dump(function_call, f)
                
                # Run the mcp-knowledge-graph CLI command with explicit path
                logger.debug(f"Executing MCP via CLI: {MCP_EXECUTABLE} --memory-path {self.memory_path} --function {input_file}")
                process = await asyncio.create_subprocess_exec(
                    MCP_EXECUTABLE,
                    "--memory-path", self.memory_path,
                    "--function", input_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                # Clean up the temporary file
                try:
                    os.remove(input_file)
                except:
                    pass
                
                if process.returncode != 0:
                    error = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"MCP CLI error: {error}")
                    raise Exception(f"MCP function call failed: {error}")
                
                # Parse the result
                result = json.loads(stdout.decode())
                return result
            
            # Use existing process if available
            if self.mcp_process:
                # Send the function call to the server
                message = json.dumps(function_call) + "\n"
                self.mcp_process.stdin.write(message.encode())
                await self.mcp_process.stdin.drain()
                
                # Read the response
                response_line = await self.mcp_process.stdout.readline()
                response = json.loads(response_line.decode())
                
                return response
                
            raise Exception("No MCP server connection available")
        except Exception as e:
            logger.error(f"Error calling MCP function {function_name}: {str(e)}")
            raise

    # Convenience methods for common operations
    
    async def create_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple new entities in the knowledge graph.
        """
        return await self.call_function("create_entities", {"entities": entities})
    
    async def create_relations(self, relations: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Create multiple new relations between entities.
        """
        return await self.call_function("create_relations", {"relations": relations})
    
    async def add_observations(self, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add new observations to existing entities.
        """
        return await self.call_function("add_observations", {"observations": observations})
    
    async def read_graph(self) -> Dict[str, Any]:
        """
        Read the entire knowledge graph.
        """
        return await self.call_function("read_graph", {"random_string": "dummy"})
    
    async def search_nodes(self, query: str) -> Dict[str, Any]:
        """
        Search for nodes based on a query.
        """
        return await self.call_function("search_nodes", {"query": query})
    
    async def open_nodes(self, names: List[str]) -> Dict[str, Any]:
        """
        Open specific nodes by name.
        """
        return await self.call_function("open_nodes", {"names": names})
    
    async def delete_entities(self, entity_names: List[str]) -> Dict[str, Any]:
        """
        Delete multiple entities and their relations.
        """
        return await self.call_function("delete_entities", {"entityNames": entity_names})
    
    async def delete_observations(self, deletions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Delete specific observations from entities.
        """
        return await self.call_function("delete_observations", {"deletions": deletions})
    
    async def delete_relations(self, relations: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Delete specific relations.
        """
        return await self.call_function("delete_relations", {"relations": relations})

# Create a singleton instance
memory_service = MemoryService() 