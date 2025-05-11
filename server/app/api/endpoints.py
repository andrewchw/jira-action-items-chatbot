from fastapi import APIRouter, HTTPException, Depends, Request, status
from typing import Dict, List, Optional, Any
import logging
import json
import os
from datetime import datetime, timedelta
import dateparser
from app.services.memory import memory_service
from app.models.database import get_db, create_reminder, get_pending_reminders, JiraCache, Reminder, UserConfig, JiraUserCache
from app.models.schemas import ReminderRequest, ReminderResponse, ReminderList, ChatMessage, ChatResponse, ReminderModel, ReminderActionResponse
from app.services.llm import llm_service
from app.services.prompts import prompt_manager
from app.services.jira import JiraClient, create_jira_issue
from app.core.config import settings
from sqlalchemy.orm import Session
import hashlib
from app.api.auth import get_current_user
import re
from sqlalchemy import or_, func

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the Jira client
jira_client = JiraClient()

# Helper function to get a Jira client (either OAuth or basic auth)
def get_jira_client(request = None, db = None):
    """
    Get a Jira client using OAuth token if available, otherwise fallback to basic auth.
    
    Args:
        request: FastAPI request object (for extracting user from cookies)
        db: Database session
        
    Returns:
        JiraClient instance
    """
    if request and db:
        # Try to get user ID from cookie
        user_id = request.cookies.get("jira_user_id")
        
        if user_id:
            # Create OAuth client
            client = JiraClient(use_oauth=True, user_id=user_id)
            
            # Try to load OAuth token
            if client.load_oauth_token(db):
                logger.info(f"Using OAuth for user {user_id}")
                return client
                
            logger.info(f"OAuth token not available for user {user_id}, falling back to basic auth")
    
    # Fall back to basic auth client
    return jira_client

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint to verify the server is running.
    
    Returns:
        Status information including server version
    """
    return {
        "status": "ok",
        "version": settings.API_VERSION,
        "server": "Jira Action Items Chatbot API"
    }

@router.get("/settings")
async def get_settings():
    """
    Get server settings that the client needs to know about.
    
    Returns:
        Dictionary of settings for the client
    """
    return {
        "settings": {
            "DEFAULT_JIRA_PROJECT_KEY": settings.DEFAULT_JIRA_PROJECT_KEY,
            "API_VERSION": settings.API_VERSION,
            "JIRA_URL": settings.JIRA_URL
        }
    }

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
    request: Request,
    jql: str = "assignee = currentUser() ORDER BY updated DESC",
    max_results: int = 50,
    fields: Optional[str] = None,
    use_cache: bool = True,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Jira tasks using JQL query.
    
    Args:
        jql: JQL query string (default: tasks assigned to current user)
        max_results: Maximum number of results to return
        fields: Comma-separated list of fields to include
        use_cache: Whether to use cached results
    """
    try:
        # Get Jira client with OAuth if available
        client = get_jira_client(request, db)
        
        # Convert fields string to list if provided
        fields_list = fields.split(",") if fields else None
        
        # Call the Jira API
        result = client.search_issues(
            jql=jql,
            fields=fields_list,
            max_results=max_results,
            use_cache=use_cache
        )
        
        # Map Jira fields to natural language entities for better presentation
        if "issues" in result:
            for i, issue in enumerate(result["issues"]):
                result["issues"][i]["entities"] = client.map_jira_to_nl_entities(issue)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching Jira tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira tasks: {str(e)}")

@router.post("/jira/tasks")
async def create_jira_task(
    request: Request,
    task: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new Jira task.
    
    Args:
        task: Task details including project, type, summary, etc.
    """
    try:
        # Log the incoming request
        logger.info(f"Creating Jira task with data: {json.dumps(task, default=str)}")
        
        # Check for user_id in the task data for OAuth authentication
        user_id = task.get("user_id")
        
        # Get Jira client with OAuth if available
        client = get_jira_client(request, db)
        
        # Extract required fields
        project_key = task.get("project_key")
        if not project_key:
            project_key = settings.DEFAULT_JIRA_PROJECT_KEY
            if not project_key:
                raise HTTPException(status_code=400, detail="Project key is required")
            logger.info(f"Using default project key: {project_key}")
        
        issue_type = task.get("issue_type", "Task")
        
        # Handle the summary/title field (accept either)
        summary = task.get("summary")
        if not summary:
            summary = task.get("title")
        if not summary:
            raise HTTPException(status_code=400, detail="Summary or title is required")
        
        description = task.get("description", "")
        
        # Extract additional fields
        additional_fields = {}
        field_mapping = {
            "priority": "priority",
            "assignee": "assignee",
            "labels": "labels",
            "components": "components",
            "due_date": "duedate",  # Map due_date to duedate which Jira expects
            "duedate": "duedate",   # Allow direct duedate field too
            "fixVersions": "fixVersions",
            "versions": "versions"
        }
        
        for key, value in task.items():
            # Skip already handled fields and null/empty values
            if key in ["project_key", "issue_type", "summary", "title", "description", "user_id"] or value is None or value == "":
                continue
            
            # Map field name if needed
            mapped_key = field_mapping.get(key, key)
            additional_fields[mapped_key] = value
            
        # Log what we're about to send to Jira
        logger.info(f"Creating Jira issue in project {project_key} with type {issue_type}")
        logger.debug(f"Summary: {summary}")
        logger.debug(f"Additional fields: {json.dumps(additional_fields, default=str)}")
        
        # Create the issue
        result = client.create_issue(
            project_key=project_key,
            issue_type=issue_type,
            summary=summary,
            description=description,
            additional_fields=additional_fields
        )
        
        # Log success and return the result
        logger.info(f"Successfully created Jira issue: {result.get('key', 'Unknown key')}")
        return {"success": True, "data": result}
    except HTTPException as he:
        # Re-raise HTTP exceptions
        logger.error(f"HTTP error creating Jira task: {str(he.detail)}")
        raise
    except Exception as e:
        # Handle other exceptions
        error_message = str(e)
        logger.error(f"Error creating Jira task: {error_message}")
        logger.error("Error stack trace:", exc_info=True)
        
        # Return a structured error response
        return {
            "success": False,
            "error": error_message,
            "message": "Failed to create Jira task"
        }

@router.get("/jira/tasks/{issue_key}")
async def get_jira_task(
    issue_key: str,
    fields: Optional[str] = None,
    use_cache: bool = True,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get details for a specific Jira task.
    
    Args:
        issue_key: The issue key (e.g., 'PROJECT-123')
        fields: Comma-separated list of fields to include
        use_cache: Whether to use cached results
    """
    try:
        # Convert fields string to list if provided
        fields_list = fields.split(",") if fields else None
        
        # Call the Jira API
        result = jira_client.get_issue(
            issue_key=issue_key,
            fields=fields_list
        )
        
        # Add natural language entities
        result["entities"] = jira_client.map_jira_to_nl_entities(result)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira task {issue_key}: {str(e)}")

@router.put("/jira/tasks/{issue_key}")
async def update_jira_task(
    issue_key: str,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update a Jira task.
    
    Args:
        issue_key: The issue key (e.g., 'PROJECT-123')
        updates: Fields to update
    """
    try:
        # Map natural language entities to Jira fields if provided
        if "entities" in updates:
            jira_fields = jira_client.map_nl_to_jira_fields(updates["entities"])
            updates = jira_fields
        
        # Update the issue
        result = jira_client.update_issue(
            issue_key=issue_key,
            fields=updates
        )
        
        # Get updated issue
        updated_issue = jira_client.get_issue(issue_key=issue_key)
        
        return updated_issue
    except Exception as e:
        logger.error(f"Error updating Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update Jira task {issue_key}: {str(e)}")

@router.post("/jira/tasks/{issue_key}/comment")
async def add_jira_comment(
    issue_key: str,
    comment_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Add a comment to a Jira task.
    
    Args:
        issue_key: The issue key (e.g., 'PROJECT-123')
        comment_data: Comment details including body and visibility
    """
    try:
        # Extract comment body
        comment = comment_data.get("body")
        if not comment:
            raise HTTPException(status_code=400, detail="Comment body is required")
        
        # Extract visibility if provided
        visibility = comment_data.get("visibility")
        
        # Add the comment
        result = jira_client.add_comment(
            issue_key=issue_key,
            comment=comment,
            visibility=visibility
        )
        
        return result
    except Exception as e:
        logger.error(f"Error adding comment to Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add comment to Jira task {issue_key}: {str(e)}")

@router.post("/jira/tasks/{issue_key}/transition")
async def transition_jira_task(
    issue_key: str,
    transition_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Transition a Jira task to a new status.
    
    Args:
        issue_key: The issue key (e.g., 'PROJECT-123')
        transition_data: Transition details including ID, comment, and fields
    """
    try:
        # Extract transition ID
        transition_id = transition_data.get("id")
        if not transition_id:
            # Try to get transition by name
            transition_name = transition_data.get("name")
            if not transition_name:
                raise HTTPException(status_code=400, detail="Transition ID or name is required")
            
            # Get available transitions
            transitions = jira_client.get_issue_transitions(issue_key)
            
            # Find transition by name
            for transition in transitions.get("transitions", []):
                if transition["name"].lower() == transition_name.lower():
                    transition_id = transition["id"]
                    break
            
            if not transition_id:
                raise HTTPException(status_code=400, detail=f"Transition '{transition_name}' not found")
        
        # Extract comment if provided
        comment = transition_data.get("comment")
        
        # Extract fields if provided
        fields = transition_data.get("fields")
        
        # Transition the issue
        result = jira_client.transition_issue(
            issue_key=issue_key,
            transition_id=transition_id,
            comment=comment,
            fields=fields
        )
        
        # Get updated issue
        updated_issue = jira_client.get_issue(issue_key=issue_key)
        
        return updated_issue
    except Exception as e:
        logger.error(f"Error transitioning Jira task {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to transition Jira task {issue_key}: {str(e)}")

@router.get("/jira/projects")
async def get_jira_projects(
    use_cache: bool = True,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all Jira projects.
    
    Args:
        use_cache: Whether to use cached results
    """
    try:
        # Call the Jira API
        result = jira_client.get_projects()
        
        return result
    except Exception as e:
        logger.error(f"Error fetching Jira projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira projects: {str(e)}")

@router.get("/jira/issue-types")
async def get_jira_issue_types(
    use_cache: bool = True,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all Jira issue types.
    
    Args:
        use_cache: Whether to use cached results
    """
    try:
        # Call the Jira API
        result = jira_client.get_issue_types()
        
        return result
    except Exception as e:
        logger.error(f"Error fetching Jira issue types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira issue types: {str(e)}")

@router.post("/jira/extract")
async def extract_jira_entities(
    text_data: Dict[str, str],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Extract Jira entities from text using NLP processing.
    
    Args:
        text_data: Text to process
    """
    try:
        # Extract text
        text = text_data.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Extract Jira issue key if present
        issue_key = jira_client.extract_issue_key_from_text(text)
        
        # Extract project key if present
        project_key = jira_client.extract_project_key_from_text(text)
        
        # Use LLM to extract other entities
        entities = prompt_manager.extract_jira_entities(text)
        
        # Add extracted keys
        if issue_key:
            entities["issue_key"] = issue_key
        
        if project_key:
            entities["project_key"] = project_key
        
        return {"entities": entities}
    except Exception as e:
        logger.error(f"Error extracting Jira entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract Jira entities: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def process_chat_message(message: ChatMessage, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Process a user chat message using LLM service and return response.
    
    Args:
        message: Chat message with user's text
        db: Database session
        
    Returns:
        Chat response with LLM's reply
    """
    # Track execution time
    start_time = datetime.now()
    
    try:
        # Get user input
        sanitized_text = message.text.strip()
        
        # Skip empty messages
        if not sanitized_text:
            return ChatResponse(
                response="I didn't receive any message. Please try again.",
                timestamp=datetime.now()
            )
            
        # Get optional conversation history safely using getattr with default
        history = getattr(message, 'history', [])
        
        # Process user input to determine intent and extract entities
        try:
            from app.services.prompts import PromptManager
            intent_result = PromptManager.process_user_input(sanitized_text)
            
            intent = intent_result.get("intent", "general_chat")
            entities = intent_result.get("entities", {})
            messages = intent_result.get("messages", [])
            
            logger.info(f"Detected intent: {intent} from message: {sanitized_text[:50]}...")
            logger.debug(f"Extracted entities: {entities}")
        except Exception as intent_error:
            logger.error(f"Error processing intent: {str(intent_error)}")
            # Default to general chat on error
            intent = "general_chat"
            entities = {}
            messages = []
            
        # Action storage
        actions = []
        
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
                        "contents": [f"Asked about: {sanitized_text[:50]}..."]
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
        
        # Process Jira-related queries using Jira client (with caching)
        jira_context = None
        jira_related = intent in [
            "get_tasks", "get_task_details", "get_my_tasks", "create_task",
            "update_task", "add_comment", "transition_task", "assign_task"
        ]
        
        if jira_related:
            try:
                # Determine which Jira method to call based on intent
                if intent == "get_task_details" and "task_id" in entities:
                    # Get details for a specific task from cached database if possible
                    task_id = entities["task_id"]
                    
                    # Try to get the task from cache first (with 30 min TTL)
                    jira_context = jira_client._check_jira_cache(task_id, max_age_minutes=30)
                    
                    # If not in cache, get from API and cache it
                    if not jira_context:
                        jira_context = jira_client.get_issue(task_id)
                    
                    # Format Jira context as a message for the LLM
                    if jira_context:
                        # Add structured Jira data to the context
                        jira_message = {
                            "role": "system", 
                            "content": f"Jira task details: {json.dumps(jira_context, default=str)}"
                        }
                        messages.insert(2, jira_message)
                
                elif intent == "get_my_tasks" or intent == "get_tasks":
                    # Build JQL query based on entities
                    jql = "ORDER BY updated DESC"
                    
                    if "assignee" in entities:
                        jql = f"assignee = '{entities['assignee']}' {jql}"
                    else:
                        jql = f"assignee = currentUser() {jql}"
                    
                    if "status_filter" in entities:
                        jql = f"status = '{entities['status_filter']}' AND {jql}"
                    
                    # Cache key for this specific JQL
                    cache_key = f"jql_{hashlib.md5(jql.encode()).hexdigest()}"
                    
                    # Try to get from cache first (with 10 min TTL)
                    jira_context = jira_client._check_jira_cache(cache_key, max_age_minutes=10)
                    
                    # If not in cache, get from API and cache it
                    if not jira_context:
                        jira_context = jira_client.search_issues(jql, max_results=10)
                        # Save to cache
                        jira_client._save_to_jira_cache(cache_key, jira_context)
                    
                    # Format the results for the LLM
                    if jira_context:
                        # Add structured Jira data to the context
                        jira_message = {
                            "role": "system", 
                            "content": f"Jira tasks: {json.dumps(jira_context, default=str)}"
                        }
                        messages.insert(2, jira_message)
                
                elif intent == "create_task":
                    # Handle intent-specific actions
                    actions = []
                    try:
                        # Basic validation check
                        if not entities.get("summary") and not entities.get("title"):
                            raise ValueError("Task summary or title is required")
                        
                        # Normalize title/summary fields
                        if entities.get("title") and not entities.get("summary"):
                            entities["summary"] = entities["title"]
                        elif entities.get("summary") and not entities.get("title"):
                            entities["title"] = entities["summary"]
                            
                        # Convert day name to date if needed
                        if entities.get("due_date"):
                            try:
                                parsed_date = parse_due_date(entities["due_date"])
                                if parsed_date:
                                    logger.debug(f"Converted day name '{entities['due_date']}' to date '{parsed_date}'")
                                    entities["due_date"] = parsed_date
                            except Exception as date_err:
                                logger.warning(f"Error parsing due date: {str(date_err)}")
                        
                        logger.info(f"Creating Jira issue with data: {json.dumps(entities)}")
                        
                        # Create Jira issue
                        response = create_jira_issue(entities)
                        
                        if response and response.get("key"):
                            # Success - add success message and action
                            issue_key = response.get("key")
                            issue_id = response.get("id")
                            
                            # Create action for viewing the issue
                            actions.append({
                                "action": "view_task",
                                "text": f"View {issue_key}",
                                "url": f"{os.getenv('JIRA_URL', 'https://your-domain.atlassian.net')}/browse/{issue_key}"
                            })
                            
                            # Add to response
                            summary = response.get("summary", entities.get("summary", entities.get("title", "")))
                            assignee_info = ""
                            if response.get("assignee") or entities.get("assignee"):
                                assignee = response.get("assignee") or entities.get("assignee")
                                assignee_info = f" and assigned to {assignee}"
                            
                            response_text = f"✅ I've created Jira task {issue_key}{assignee_info}: {summary}. You can click the button below to view it."
                            
                            # Store in memory if possible
                            try:
                                await memory_service.add_observations([
                                    {
                                        "entityName": f"jira_issue_{issue_key}",
                                        "contents": [
                                            f"Created task {issue_key} with summary: {summary}",
                                            f"Issue type: {response.get('issue_type', entities.get('issue_type', 'Task'))}",
                                            f"Created at: {datetime.now().isoformat()}"
                                        ]
                                    }
                                ])
                            except Exception as memory_err:
                                logger.warning(f"Error adding task to memory: {str(memory_err)}")
                        else:
                            # Failed
                            error_message = response.get("error", "Unknown error")
                            response_text = f"❌ I had difficulty creating your Jira task: {error_message}"
                            
                            # Add retry action
                            actions.append({
                                "action": "create_task",
                                "text": "Try Again",
                                "params": entities
                            })
                    except Exception as create_err:
                        logger.error(f"Error creating Jira task: {str(create_err)}", exc_info=True)
                        response_text = f"❌ I encountered an error while creating your task: {str(create_err)}"
                        
                        # Add retry action
                        actions.append({
                            "action": "create_task",
                            "text": "Try Again",
                            "params": entities
                        })
                
                # Add similar logic for other Jira intents...
                
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
            try:
                if not llm_response or "choices" not in llm_response or not llm_response["choices"]:
                    logger.error(f"LLM service error: Invalid response format - {llm_response}")
                    response_text = "I'm sorry, I encountered an issue processing your request. Please try again or rephrase your query."
                else:
                    response_text = llm_response["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"LLM service error: {str(e)}")
                response_text = "I'm sorry, I encountered an issue processing your request. Please try again or rephrase your query."
            
            # Generate suggested actions based on intent and entities
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
                
                # Add action to update the task status if available
                if jira_context and "fields" in jira_context and "status" in jira_context["fields"]:
                    current_status = jira_context["fields"]["status"]["name"]
                    available_transitions = jira_client.get_transitions(task_id)
                    
                    for transition in available_transitions.get("transitions", [])[:3]:  # Limit to first 3
                        actions.append({
                            "type": "button",
                            "text": f"Move to {transition['name']}",
                            "action": "transition",
                            "params": {
                                "task_id": task_id,
                                "transition_id": transition["id"],
                                "transition_name": transition["name"]
                            }
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
                
                # Add quick create action
                actions.append({
                    "type": "button",
                    "text": "Quick Create",
                    "action": "create_task",
                    "params": {
                        "project_key": project_key,
                        "title": entities["title"],
                        "description": entities.get("description", ""),
                        "priority": entities.get("priority", "Medium")
                    }
                })
                
            elif intent in ["get_tasks", "get_my_tasks"]:
                # Add action to view all tasks in Jira
                actions.append({
                    "type": "button",
                    "text": "View All in Jira",
                    "url": f"{settings.JIRA_URL}/issues/"
                })
                
                # Add project-specific view if a project was mentioned
                if "project_key" in entities:
                    project_key = entities["project_key"]
                    actions.append({
                        "type": "button",
                        "text": f"View {project_key} Tasks",
                        "url": f"{settings.JIRA_URL}/projects/{project_key}/issues/"
                    })
            
            # Format the response text based on content type
            # Clean up any markdown artifacts or formatting issues from LLM
            response_text = response_text.replace("```", "").strip()
            
            # Add execution time for debugging
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Chat request processed in {execution_time:.2f} seconds")
            
            return ChatResponse(
                response=response_text,
                actions=actions if actions else None,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}")
            
            # Use fallback response with detailed context
            fallback_message = await llm_service.fallback_response(sanitized_text)
            
            # Add additional context if it's a Jira-related error
            if jira_related:
                fallback_message += "\n\nThere seems to be an issue with the Jira integration. Please try again later or access Jira directly."
            
            return ChatResponse(
                response=fallback_message,
                timestamp=datetime.now()
            )
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing chat message: {error_message}")
        logger.error(f"Error stack trace:", exc_info=True)
        
        try:
            # Try to extract useful information from the error message
            if "JSONDecodeError" in error_message:
                error_message = "Failed to parse JSON response from LLM. This may be due to an issue with the service."
            elif "timeout" in error_message.lower():
                error_message = "Request timed out. Please try again."
            elif "connection" in error_message.lower():
                error_message = "Connection error. Please check your internet connection and try again."
            elif "authentication" in error_message.lower() or "unauthorized" in error_message.lower() or "401" in error_message:
                error_message = "Authentication error. Please check your credentials."
            elif "permission" in error_message.lower() or "forbidden" in error_message.lower() or "403" in error_message:
                error_message = "Permission denied. You don't have access to this resource."
            elif "not found" in error_message.lower() or "404" in error_message:
                error_message = "Resource not found. Please check your request."
            
            # Prepare a friendly response
            friendly_response = f"I'm sorry, I encountered an error processing your request. {error_message}"
            
            # Return a friendly error message
            return ChatResponse(
                response=friendly_response,
                timestamp=datetime.now()
            )
        except Exception as response_error:
            # Last resort fallback
            logger.error(f"Error creating error response: {str(response_error)}")
            return ChatResponse(
                response="I'm sorry, I encountered an unexpected error. Please try again later.",
                timestamp=datetime.now()
            )

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

# Add a user info endpoint for frontend compatibility
@router.get("/user")
async def get_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get current user info. This endpoint is provided for frontend compatibility.
    """
    try:
        user_id = request.cookies.get("jira_user_id")
        logger.info(f"Getting user info for user_id: {user_id}")
        
        if not user_id:
            logger.warning("No user_id cookie found")
            return {
                "authenticated": False, 
                "message": "Not authenticated"
            }
        
        user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
        
        if not user_config or not user_config.jira_user_info:
            logger.warning(f"No user config or user info found for user_id: {user_id}")
            return {
                "authenticated": False, 
                "message": "User data not found"
            }
        
        # Parse the stored user info
        user_info = json.loads(user_config.jira_user_info)
        
        return {
            "authenticated": True,
            "user": user_info,
            "jira_access_token": "***REDACTED***"  # Don't send the actual token to client
        }
    except Exception as e:
        logger.error(f"Error in get_user_info: {str(e)}")
        return {
            "authenticated": False,
            "error": str(e)
        }

# Helper function to parse due dates from various formats
def parse_due_date(date_str: str) -> str:
    """
    Parse a due date string into Jira-compatible format (YYYY-MM-DD).
    
    Args:
        date_str: Date string in various formats (e.g., 'tomorrow', 'next Monday', 'Friday', '2023-05-15')
        
    Returns:
        Formatted date string (YYYY-MM-DD) or original string if parsing fails
    """
    try:
        # Try to parse the date string using dateparser
        parsed_date = dateparser.parse(
            date_str, 
            settings={'PREFER_DATES_FROM': 'future', 'DATE_ORDER': 'YMD'}
        )
        
        if parsed_date:
            # Format as YYYY-MM-DD for Jira
            return parsed_date.strftime('%Y-%m-%d')
        
        # Return original string if parsing fails
        return date_str
    except Exception as e:
        logger.warning(f"Error parsing due date '{date_str}': {str(e)}")
        return date_str 

# Add this new endpoint to sync Jira users and retrieve cached users

@router.post("/jira/sync-users")
async def sync_jira_users(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sync Jira users to local database.
    
    Returns:
        Dictionary with results of sync operation
    """
    try:
        # Get Jira client
        client = JiraClient()
        
        # Sync users
        result = client.sync_users(db)
        
        # Return result
        return result
    except Exception as e:
        logger.error(f"Error syncing Jira users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing Jira users: {str(e)}"
        )

@router.get("/jira/users")
async def get_jira_users(
    query: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Jira users from local database.
    
    Args:
        query: Optional search query to filter users
        limit: Maximum number of users to return
        
    Returns:
        Dictionary with list of users
    """
    try:
        from app.models.database import JiraUserCache
        
        # Build query
        db_query = db.query(JiraUserCache)
        
        # Apply search filter if provided
        if query:
            query_lower = query.lower()
            db_query = db_query.filter(
                or_(
                    func.lower(JiraUserCache.username).contains(query_lower),
                    func.lower(JiraUserCache.display_name).contains(query_lower),
                    func.lower(JiraUserCache.email).contains(query_lower)
                )
            )
        
        # Order by display name and limit results
        users = db_query.order_by(JiraUserCache.display_name).limit(limit).all()
        
        # Format response
        result = []
        for user in users:
            result.append({
                "id": user.id,
                "account_id": user.account_id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "active": user.active,
                "last_updated": user.last_updated.isoformat() if user.last_updated else None
            })
        
        return {
            "success": True,
            "count": len(result),
            "users": result
        }
    except Exception as e:
        logger.error(f"Error getting Jira users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting Jira users: {str(e)}"
        ) 