"""
Simple API server that provides memory graph functionality without requiring MCP.
This is a fallback for when the MCP knowledge graph server isn't available.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from http.server import HTTPServer, BaseHTTPRequestHandler

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
            if not self.memory_path:
                logger.warning("No memory path provided")
                return
                
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
            if not self.memory_path:
                logger.warning("No memory path provided, not saving")
                return
                
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

# Create a global memory graph
memory_graph = SimpleInMemoryGraph("memory.jsonl")

class MemoryHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for memory graph API requests"""
    
    def _set_headers(self, content_type="application/json", status_code=200):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            # Health check endpoint
            response = {"status": "healthy"}
            self._set_headers()
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/api/memory/status":
            # Memory status endpoint
            response = {
                "status": "connected",
                "memory_path": memory_graph.memory_path,
                "mode": "in-memory",
                "entity_count": len(memory_graph.entities)
            }
            self._set_headers()
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/api/memory/graph":
            # Read entire graph
            response = memory_graph.read_graph()
            self._set_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            # Not found
            self._set_headers(status_code=404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            
            if self.path == "/api/memory/entities":
                # Create entities
                if "entities" in data:
                    response = memory_graph.create_entities(data["entities"])
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(status_code=400)
                    self.wfile.write(json.dumps({"error": "Missing entities field"}).encode())
            elif self.path == "/api/memory/relations":
                # Create relations
                if "relations" in data:
                    response = memory_graph.create_relations(data["relations"])
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(status_code=400)
                    self.wfile.write(json.dumps({"error": "Missing relations field"}).encode())
            elif self.path == "/api/memory/observations":
                # Add observations
                if "observations" in data:
                    response = memory_graph.add_observations(data["observations"])
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(status_code=400)
                    self.wfile.write(json.dumps({"error": "Missing observations field"}).encode())
            elif self.path == "/api/memory/search":
                # Search nodes
                if "query" in data:
                    response = memory_graph.search_nodes(data["query"])
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(status_code=400)
                    self.wfile.write(json.dumps({"error": "Missing query field"}).encode())
            elif self.path == "/api/memory/nodes":
                # Open nodes
                if "names" in data:
                    response = memory_graph.open_nodes(data["names"])
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(status_code=400)
                    self.wfile.write(json.dumps({"error": "Missing names field"}).encode())
            else:
                # Not found
                self._set_headers(status_code=404)
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
        except json.JSONDecodeError:
            self._set_headers(status_code=400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            self._set_headers(status_code=500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
        
        try:
            data = {}
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
            
            if self.path == "/api/memory/entities":
                # Delete entities
                if "entityNames" in data:
                    response = memory_graph.delete_entities(data["entityNames"])
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(status_code=400)
                    self.wfile.write(json.dumps({"error": "Missing entityNames field"}).encode())
            elif self.path == "/api/memory/observations":
                # Delete observations
                if "deletions" in data:
                    response = memory_graph.delete_observations(data["deletions"])
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(status_code=400)
                    self.wfile.write(json.dumps({"error": "Missing deletions field"}).encode())
            elif self.path == "/api/memory/relations":
                # Delete relations
                if "relations" in data:
                    response = memory_graph.delete_relations(data["relations"])
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self._set_headers(status_code=400)
                    self.wfile.write(json.dumps({"error": "Missing relations field"}).encode())
            else:
                # Not found
                self._set_headers(status_code=404)
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
        except json.JSONDecodeError:
            self._set_headers(status_code=400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            self._set_headers(status_code=500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

def run_server(port=8000):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MemoryHTTPHandler)
    logger.info(f"Starting memory API server on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    # Get port from command line argument if provided
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    # Get memory path from command line argument if provided
    memory_path = "memory.jsonl"
    if len(sys.argv) > 2:
        memory_path = sys.argv[2]
    
    # Initialize memory graph with provided path
    memory_graph.memory_path = memory_path
    memory_graph._load_memory()
    
    # Run server
    run_server(port) 