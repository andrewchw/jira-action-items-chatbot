from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
import logging
import json
import os
from datetime import datetime, timedelta
from app.services.memory import memory_service
from app.models.database import get_db, create_reminder, get_pending_reminders, JiraCache, Reminder, UserConfig
from app.models.schemas import ReminderRequest, ReminderResponse, ReminderList, ChatMessage, ChatResponse
from app.services.llm import llm_service
from app.services.prompts import prompt_manager
from app.services.jira import JiraClient
from app.core.config import settings
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the Jira client
jira_client = JiraClient()

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

# Jira API Integration Endpoints

@router.get("/jira/tasks")
async def get_jira_tasks(
    jql: str = "assignee = currentUser() ORDER BY updated DESC",
    max_results: int = 50,
    fields: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get Jira tasks using JQL query.
    
    Args:
        jql: JQL query string (default: tasks assigned to current user)
        max_results: Maximum number of results to return
        fields: Comma-separated list of fields to include
    """
    try:
        # Convert fields string to list if provided
        fields_list = fields.split(",") if fields else None
        
        # Call the Jira API
        result = jira_client.search_issues(
            jql=jql,
            fields=fields_list,
            max_results=max_results
        )
        
        # Cache the result in the database for offline access
        # TODO: Implement caching logic
        
        return result
    except Exception as e:
        logger.error(f"Error fetching Jira tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira tasks: {str(e)}")

@router.get("/jira/task/{issue_key}")
async def get_jira_task(issue_key: str, fields: Optional[str] = None) -> Dict[str, Any]:
    """
    Get details for a specific Jira task.
    
    Args:
        issue_key: The Jira issue key (e.g., PROJ-123)
        fields: Comma-separated list of fields to include
    """
    try:
        # Convert fields string to list if provided
        fields_list = fields.split(",") if fields else None
        
        # Call the Jira API
        result = jira_client.get_issue(
            issue_key=issue_key,
            fields=fields_list
        )
        
        return result
    except Exception as e:
        logger.error(f"Error fetching Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira task: {str(e)}")

@router.post("/jira/task")
async def create_jira_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new Jira task.
    
    Args:
        task_data: Dictionary containing task details
            - project_key: Project key
            - issue_type: Issue type
            - summary: Task summary
            - description: Task description
            - additional_fields: Additional fields to set
    """
    try:
        # Extract required fields
        project_key = task_data.pop("project_key")
        issue_type = task_data.pop("issue_type", "Task")
        summary = task_data.pop("summary")
        description = task_data.pop("description", None)
        
        # Call the Jira API
        result = jira_client.create_issue(
            project_key=project_key,
            issue_type=issue_type,
            summary=summary,
            description=description,
            additional_fields=task_data.get("additional_fields", {})
        )
        
        return result
    except KeyError as e:
        logger.error(f"Missing required field for Jira task creation: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating Jira task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create Jira task: {str(e)}")

@router.put("/jira/task/{issue_key}")
async def update_jira_task(issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing Jira task.
    
    Args:
        issue_key: The Jira issue key (e.g., PROJ-123)
        fields: Dictionary of fields to update
    """
    try:
        # Call the Jira API
        result = jira_client.update_issue(
            issue_key=issue_key,
            fields=fields
        )
        
        return result
    except Exception as e:
        logger.error(f"Error updating Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update Jira task: {str(e)}")

@router.post("/jira/task/{issue_key}/comment")
async def add_comment_to_task(issue_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a comment to a Jira task.
    
    Args:
        issue_key: The Jira issue key
        data:
            - comment: Comment text
            - visibility: Optional visibility restrictions
    """
    try:
        # Extract required fields
        comment = data.get("comment")
        visibility = data.get("visibility")
        
        if not comment:
            raise HTTPException(status_code=400, detail="Comment text is required")
        
        # Call the Jira API
        result = jira_client.add_comment(
            issue_key=issue_key,
            comment=comment,
            visibility=visibility
        )
        
        return result
    except Exception as e:
        logger.error(f"Error adding comment to Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")

@router.post("/jira/task/{issue_key}/transition")
async def transition_task(issue_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transition a Jira task to a new status.
    
    Args:
        issue_key: The Jira issue key
        data:
            - transition_id: ID of the transition to perform
            - comment: Optional comment to add
            - fields: Optional fields to update during transition
    """
    try:
        # Extract required fields
        transition_id = data.get("transition_id")
        comment = data.get("comment")
        fields = data.get("fields")
        
        if not transition_id:
            raise HTTPException(status_code=400, detail="Transition ID is required")
        
        # Call the Jira API
        result = jira_client.transition_issue(
            issue_key=issue_key,
            transition_id=transition_id,
            comment=comment,
            fields=fields
        )
        
        return result
    except Exception as e:
        logger.error(f"Error transitioning Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to transition task: {str(e)}")

@router.post("/jira/task/{issue_key}/assign")
async def assign_task(issue_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assign a Jira task to a user.
    
    Args:
        issue_key: The Jira issue key
        data:
            - assignee: Username to assign to (or null to unassign)
    """
    try:
        # Extract assignee
        assignee = data.get("assignee")
        
        # Call the Jira API
        result = jira_client.assign_issue(
            issue_key=issue_key,
            assignee=assignee
        )
        
        return result
    except Exception as e:
        logger.error(f"Error assigning Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")

@router.get("/jira/projects")
async def get_projects() -> List[Dict]:
    """
    Get all available Jira projects.
    """
    try:
        # Call the Jira API
        result = jira_client.get_projects()
        
        return result
    except Exception as e:
        logger.error(f"Error fetching Jira projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def process_chat_message(message: ChatMessage, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Process a chat message from the extension, using LLM to generate a response.
    """
    try:
        # Process the user's message to determine intent and extract entities
        processed = prompt_manager.process_user_input(message.text)
        intent = processed["intent"]
        entities = processed["entities"]
        messages = processed["messages"]
        
        logger.info(f"Detected intent: {intent} from message: {message.text[:50]}...")
        
        # Try to retrieve user preferences from memory
        try:
            # Search for the current user in memory
            search_result = await memory_service.search_nodes("current_user")
            
            # If we found user preferences, use them to personalize the response
            if search_result and "entities" in search_result and search_result["entities"]:
                user_entity = search_result["entities"][0]
                
                # Add observation about this conversation
                await memory_service.add_observations([
                    {
                        "entityName": "current_user",
                        "contents": [f"Asked about: {message.text[:50]}..."]
                    }
                ])
        except Exception as e:
            # If memory access fails, continue without personalization
            logger.error(f"Memory access error: {str(e)}")
        
        # Include any provided context with the request
        if message.context:
            # Add relevant context to the messages
            context_message = {"role": "system", "content": f"Additional context: {json.dumps(message.context)}"}
            messages.insert(1, context_message)  # Insert after system prompt but before user message
        
        # Check if intent requires Jira API interaction
        jira_data = None
        try:
            if intent == "get_tasks" or intent == "get_my_tasks":
                # Construct JQL based on the entities
                jql = "assignee = currentUser()"
                
                if "status" in entities:
                    jql += f" AND status = '{entities['status']}'"
                    
                if "priority" in entities:
                    jql += f" AND priority = '{entities['priority']}'"
                    
                if "project_key" in entities:
                    jql += f" AND project = {entities['project_key']}"
                    
                jql += " ORDER BY updated DESC"
                
                # Get tasks from Jira
                jira_data = jira_client.search_issues(jql=jql, max_results=10)
                
                # Add task data to the messages as system context
                if jira_data and "issues" in jira_data:
                    jira_context = {"role": "system", "content": f"Current Jira tasks: {json.dumps(jira_data['issues'][:5])}"}
                    messages.insert(2, jira_context)  # Insert after any existing context
                    
            elif intent == "get_task_details" and "task_id" in entities:
                # Get task details from Jira
                task_id = entities["task_id"]
                jira_data = jira_client.get_issue(issue_key=task_id)
                
                # Add task data to the messages as system context
                if jira_data:
                    jira_context = {"role": "system", "content": f"Task details: {json.dumps(jira_data)}"}
                    messages.insert(2, jira_context)
            
            # For other Jira-related intents, we'll let the LLM generate a response
            # and handle the actual API calls in the appropriate endpoint
        
        except Exception as e:
            logger.error(f"Jira API error: {str(e)}")
            # Add error information to the context for the LLM
            error_context = {"role": "system", "content": f"Note: Unable to access Jira data. Error: {str(e)}"}
            messages.insert(2, error_context)
        
        # Send to LLM service
        try:
            # Try to get response from LLM
            llm_response = await llm_service.chat_completion(
                messages=messages,
                temperature=0.7,  # Use a moderate temperature for balanced responses
                use_cache=True
            )
            
            # Extract the response text
            response_text = llm_response["choices"][0]["message"]["content"]
            
            # Extract suggested actions based on intent
            actions = []
            
            # Add actions based on intent and entities
            if intent == "get_task_details" and "task_id" in entities:
                # Add action to view the task in Jira
                task_id = entities["task_id"]
                actions.append({
                    "type": "button",
                    "text": f"View {task_id} in Jira",
                    "url": f"{settings.JIRA_URL}/browse/{task_id}"
                })
                
            elif intent == "create_task" and "title" in entities:
                # Add action to create a task in Jira
                project_key = entities.get("project_key", "")
                new_task_url = f"{settings.JIRA_URL}/secure/CreateIssue.jspa"
                if project_key:
                    new_task_url += f"?pid={project_key}"
                    
                actions.append({
                    "type": "button",
                    "text": "Create in Jira",
                    "url": new_task_url
                })
                
            elif intent in ["get_tasks", "get_my_tasks"]:
                # Add action to view all tasks in Jira
                actions.append({
                    "type": "button",
                    "text": "View All in Jira",
                    "url": f"{settings.JIRA_URL}/issues/"
                })
            
            return ChatResponse(
                response=response_text,
                actions=actions if actions else None,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}")
            
            # Use fallback response
            fallback = await llm_service.fallback_response(message.text)
            return ChatResponse(
                response=fallback,
                timestamp=datetime.now()
            )
    
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

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

# Reminders Endpoints
@router.post("/reminders", response_model=ReminderResponse)
async def create_new_reminder(reminder_request: ReminderRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Create a new reminder for a Jira task.
    """
    try:
        # Check if the Jira issue exists in cache
        jira_issue = db.query(JiraCache).filter(JiraCache.issue_key == reminder_request.task_id).first()
        
        if not jira_issue:
            # Handle missing Jira issue (this would be improved with actual Jira integration)
            # For now, create a placeholder cache entry
            from app.models.database import update_jira_cache
            jira_issue = update_jira_cache(
                db=db,
                issue_key=reminder_request.task_id,
                issue_data={
                    "title": f"Issue {reminder_request.task_id}",
                    "status": "Unknown",
                    "raw_data": "{}"
                }
            )
        
        # Calculate reminder time
        reminder_time = reminder_request.reminder_time or (datetime.utcnow() + timedelta(minutes=15))
        
        # Create the reminder
        reminder = create_reminder(
            db=db,
            jira_issue_id=jira_issue.id,
            reminder_time=reminder_time,
            message=reminder_request.message,
            is_recurring=reminder_request.is_recurring,
            recurrence_pattern=reminder_request.recurrence_pattern
        )
        
        return {
            "id": reminder.id,
            "task_id": jira_issue.issue_key,
            "reminder_time": reminder.reminder_time,
            "message": reminder.message,
            "is_recurring": reminder.is_recurring,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error creating reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create reminder: {str(e)}")

@router.get("/reminders", response_model=ReminderList)
async def get_reminders(task_id: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get list of reminders, optionally filtered by task ID.
    """
    try:
        query = db.query(Reminder).join(JiraCache)
        
        if task_id:
            query = query.filter(JiraCache.issue_key == task_id)
        
        reminders = query.all()
        
        result = []
        for reminder in reminders:
            result.append({
                "id": reminder.id,
                "task_id": reminder.jira_issue.issue_key,
                "reminder_time": reminder.reminder_time,
                "message": reminder.message,
                "is_recurring": reminder.is_recurring,
                "is_sent": reminder.is_sent,
                "recurrence_pattern": reminder.recurrence_pattern
            })
        
        return {"reminders": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch reminders: {str(e)}")

@router.put("/reminders/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(reminder_id: int, reminder_request: ReminderRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Update an existing reminder.
    """
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        
        if not reminder:
            raise HTTPException(status_code=404, detail=f"Reminder with ID {reminder_id} not found")
        
        # Update reminder fields
        if reminder_request.reminder_time:
            reminder.reminder_time = reminder_request.reminder_time
        
        if reminder_request.message is not None:
            reminder.message = reminder_request.message
        
        if reminder_request.is_recurring is not None:
            reminder.is_recurring = reminder_request.is_recurring
            
        if reminder_request.recurrence_pattern is not None:
            reminder.recurrence_pattern = reminder_request.recurrence_pattern
        
        db.commit()
        db.refresh(reminder)
        
        return {
            "id": reminder.id,
            "task_id": reminder.jira_issue.issue_key,
            "reminder_time": reminder.reminder_time,
            "message": reminder.message,
            "is_recurring": reminder.is_recurring,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update reminder: {str(e)}")

@router.delete("/reminders/{reminder_id}", response_model=Dict[str, bool])
async def delete_reminder(reminder_id: int, db: Session = Depends(get_db)) -> Dict[str, bool]:
    """
    Delete a reminder.
    """
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        
        if not reminder:
            raise HTTPException(status_code=404, detail=f"Reminder with ID {reminder_id} not found")
        
        db.delete(reminder)
        db.commit()
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete reminder: {str(e)}")

@router.post("/reminders/{reminder_id}/snooze", response_model=ReminderResponse)
async def snooze_reminder(reminder_id: int, snooze_minutes: int = 15, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Snooze a reminder by a specified number of minutes.
    """
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        
        if not reminder:
            raise HTTPException(status_code=404, detail=f"Reminder with ID {reminder_id} not found")
        
        # Calculate new reminder time
        new_time = datetime.utcnow() + timedelta(minutes=snooze_minutes)
        reminder.reminder_time = new_time
        
        # If it was already sent, mark as not sent so it will trigger again
        if reminder.is_sent:
            reminder.is_sent = False
        
        db.commit()
        db.refresh(reminder)
        
        return {
            "id": reminder.id,
            "task_id": reminder.jira_issue.issue_key,
            "reminder_time": reminder.reminder_time,
            "message": reminder.message,
            "is_recurring": reminder.is_recurring,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error snoozing reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to snooze reminder: {str(e)}")

@router.get("/reminders/pending", response_model=ReminderList)
async def get_pending_reminders_api(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get all reminders that are due but not yet sent.
    This endpoint is used by the scheduler to find reminders to send.
    """
    try:
        reminders = get_pending_reminders(db)
        
        result = []
        for reminder in reminders:
            result.append({
                "id": reminder.id,
                "task_id": reminder.jira_issue.issue_key,
                "reminder_time": reminder.reminder_time,
                "message": reminder.message,
                "is_recurring": reminder.is_recurring,
                "is_sent": reminder.is_sent,
                "recurrence_pattern": reminder.recurrence_pattern
            })
        
        return {"reminders": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Error fetching pending reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending reminders: {str(e)}") 