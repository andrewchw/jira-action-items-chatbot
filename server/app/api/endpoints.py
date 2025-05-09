from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
import logging
import json
import os
from app.services.memory import memory_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify API is running.
    """
    return {"status": "healthy"}

@router.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint to verify API is running.
    """
    return {"status": "API is running"}

@router.get("/memory/status")
async def memory_service_status() -> Dict[str, Any]:
    """
    Check the status of the memory service connection.
    """
    try:
        # Test if memory service is responsive
        result = await memory_service.read_graph()
        
        # Gather memory service info
        info = {
            "status": "connected" if result is not None else "disconnected",
            "memory_path": memory_service.memory_path,
            "mode": "fallback" if memory_service.use_fallback else "mcp",
            "entity_count": len(result.get("entities", [])) if result else 0,
            "relation_count": len(result.get("relations", [])) if result else 0
        }
        return info
    except Exception as e:
        logger.error(f"Error checking memory service status: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/jira/tasks")
async def get_jira_tasks() -> Dict[str, List]:
    """
    Get Jira tasks (placeholder - will be implemented with actual Jira integration).
    """
    # This is a placeholder that will be replaced with actual Jira API integration
    sample_tasks = [
        {"id": "JIRA-1", "title": "Implement login feature", "status": "In Progress"},
        {"id": "JIRA-2", "title": "Fix navigation bug", "status": "To Do"},
        {"id": "JIRA-3", "title": "Update documentation", "status": "Done"}
    ]
    return {"tasks": sample_tasks}

@router.post("/chat")
async def process_chat_message(message: Dict[str, str]) -> Dict[str, str]:
    """
    Process a chat message from the extension (placeholder).
    """
    if "text" not in message:
        raise HTTPException(status_code=400, detail="Message text is required")
    
    # This is a placeholder that will be replaced with actual LLM integration
    user_message = message["text"]
    
    # Try to retrieve user preferences from memory
    try:
        # Search for the current user in memory
        search_result = await memory_service.search_nodes("current_user")
        
        # If we found user preferences, use them to personalize the response
        if search_result and "entities" in search_result and search_result["entities"]:
            user_entity = search_result["entities"][0]
            
            # Add user preference to the context
            user_preferences = user_entity.get("observations", [])
            
            # Add observation about this conversation
            await memory_service.add_observations([
                {
                    "entityName": "current_user",
                    "contents": [f"Asked about: {user_message[:50]}..."]
                }
            ])
    except Exception as e:
        # If memory access fails, continue without personalization
        print(f"Memory access error: {str(e)}")
    
    if "task" in user_message.lower():
        response = "I can help you manage your tasks. What would you like to do?"
    elif "remind" in user_message.lower():
        response = "I can set a reminder for you. When would you like to be reminded?"
    elif "upload" in user_message.lower() or "file" in user_message.lower():
        response = "You can upload files as evidence for your tasks."
    else:
        response = "I'm your Jira action items assistant. I can help with tasks, reminders, and evidence uploads."
    
    return {"response": response}

# Memory Management Endpoints

@router.post("/memory/entities")
async def create_entities(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Create multiple new entities in the knowledge graph.
    """
    try:
        if "entities" not in data or not isinstance(data["entities"], list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'entities' field")
        
        result = await memory_service.create_entities(data["entities"])
        return result
    except Exception as e:
        logger.error(f"Error creating entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create entities: {str(e)}")

@router.post("/memory/relations")
async def create_relations(data: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Create multiple new relations between entities.
    """
    try:
        if "relations" not in data or not isinstance(data["relations"], list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'relations' field")
        
        result = await memory_service.create_relations(data["relations"])
        return result
    except Exception as e:
        logger.error(f"Error creating relations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create relations: {str(e)}")

@router.post("/memory/observations")
async def add_observations(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Add new observations to existing entities.
    """
    try:
        if "observations" not in data or not isinstance(data["observations"], list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'observations' field")
        
        result = await memory_service.add_observations(data["observations"])
        return result
    except Exception as e:
        logger.error(f"Error adding observations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add observations: {str(e)}")

@router.get("/memory/graph")
async def read_graph() -> Dict[str, Any]:
    """
    Read the entire knowledge graph.
    """
    try:
        result = await memory_service.read_graph()
        return result
    except Exception as e:
        logger.error(f"Error reading graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read graph: {str(e)}")

@router.post("/memory/search")
async def search_nodes(data: Dict[str, str]) -> Dict[str, Any]:
    """
    Search for nodes based on a query.
    """
    try:
        if "query" not in data or not isinstance(data["query"], str):
            raise HTTPException(status_code=400, detail="Missing or invalid 'query' field")
        
        result = await memory_service.search_nodes(data["query"])
        return result
    except Exception as e:
        logger.error(f"Error searching nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search nodes: {str(e)}")

@router.post("/memory/nodes")
async def open_nodes(data: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Open specific nodes by name.
    """
    try:
        if "names" not in data or not isinstance(data["names"], list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'names' field")
        
        result = await memory_service.open_nodes(data["names"])
        return result
    except Exception as e:
        logger.error(f"Error opening nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to open nodes: {str(e)}")

@router.delete("/memory/entities")
async def delete_entities(data: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Delete multiple entities and their associated relations.
    """
    try:
        if "entityNames" not in data or not isinstance(data["entityNames"], list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'entityNames' field")
        
        result = await memory_service.delete_entities(data["entityNames"])
        return result
    except Exception as e:
        logger.error(f"Error deleting entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete entities: {str(e)}")

@router.delete("/memory/observations")
async def delete_observations(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Delete specific observations from entities.
    """
    try:
        if "deletions" not in data or not isinstance(data["deletions"], list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'deletions' field")
        
        result = await memory_service.delete_observations(data["deletions"])
        return result
    except Exception as e:
        logger.error(f"Error deleting observations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete observations: {str(e)}")

@router.delete("/memory/relations")
async def delete_relations(data: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Delete multiple relations from the knowledge graph.
    """
    try:
        if "relations" not in data or not isinstance(data["relations"], list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'relations' field")
        
        result = await memory_service.delete_relations(data["relations"])
        return result
    except Exception as e:
        logger.error(f"Error deleting relations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete relations: {str(e)}") 