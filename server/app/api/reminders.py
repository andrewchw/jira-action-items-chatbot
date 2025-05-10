"""
API endpoints for reminder system to allow the extension to fetch and interact with reminders.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db
from app.services.reminders import reminder_service
from app.services.llm import llm_service
from app.api.auth import get_current_user

# Create router
router = APIRouter()

@router.get("/check")
async def check_reminders(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check for pending reminders for the current user.
    
    Returns:
        Dictionary with reminders list
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get pending notifications for the user
    notifications = await reminder_service.get_pending_notifications(current_user["account_id"])
    
    return {
        "reminders": notifications,
        "count": len(notifications)
    }

@router.post("/mark-done")
async def mark_reminder_done(
    request: Request,
    issue_key: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a reminder as done (transition the Jira issue).
    
    Args:
        issue_key: Jira issue key
        
    Returns:
        Result of the operation
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Get the "Done" transition ID from the issue
        from app.services.jira import JiraClient
        jira_client = JiraClient(use_oauth=True, user_id=current_user["account_id"])
        jira_client.load_oauth_token(db)
        
        # Get available transitions
        transitions = jira_client.get_issue_transitions(issue_key)
        
        # Find a "Done" transition
        done_transition = None
        for transition in transitions.get("transitions", []):
            name = transition.get("name", "").lower()
            if any(word in name for word in ["done", "complete", "resolved", "closed"]):
                done_transition = transition["id"]
                break
        
        if not done_transition:
            raise HTTPException(status_code=400, detail="No 'Done' transition available for this issue")
        
        # Apply the transition
        result = jira_client.transition_issue(
            issue_key=issue_key,
            transition_id=done_transition,
            comment="Marked as done from Jira Action Items Chatbot"
        )
        
        return {
            "success": True,
            "message": f"Issue {issue_key} marked as done"
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to mark issue as done: {str(e)}"
        }

@router.post("/snooze")
async def snooze_reminder(
    request: Request,
    issue_key: str,
    days: int = 1,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Snooze a reminder by updating the due date.
    
    Args:
        issue_key: Jira issue key
        days: Number of days to snooze
        
    Returns:
        Result of the operation
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Calculate new due date
        from datetime import datetime, timedelta
        new_due_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Update the issue due date
        from app.services.jira import JiraClient
        jira_client = JiraClient(use_oauth=True, user_id=current_user["account_id"])
        jira_client.load_oauth_token(db)
        
        result = jira_client.update_issue(
            issue_key=issue_key,
            fields={
                "duedate": new_due_date
            }
        )
        
        # Add a comment about the snooze
        jira_client.add_comment(
            issue_key=issue_key,
            comment=f"Due date updated to {new_due_date} (snoozed from Jira Action Items Chatbot)"
        )
        
        return {
            "success": True,
            "message": f"Reminder snoozed until {new_due_date}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to snooze reminder: {str(e)}"
        }

@router.post("/reply")
async def handle_conversational_reply(
    request: Request,
    issue_key: str,
    message: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handle a conversational reply to a reminder.
    Use natural language processing to determine the user's intent.
    
    Args:
        issue_key: The Jira issue key
        message: The user's reply message
        
    Returns:
        Result of the operation
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Initialize Jira client
        from app.services.jira import JiraClient
        jira_client = JiraClient(use_oauth=True, user_id=current_user["account_id"])
        jira_client.load_oauth_token(db)
        
        # Get the issue to have context
        issue = jira_client.get_issue(issue_key)
        
        # Use LLM to determine intent
        intent_prompt = f"""
        You are an AI assistant that determines user intent from a message about a Jira task.
        The user's message is in response to a reminder about the task.
        
        Task key: {issue_key}
        Task title: {issue.get("fields", {}).get("summary", "Unknown")}
        User message: "{message}"
        
        Determine the user's intent by selecting ONE of the following actions:
        - COMPLETE: The user wants to mark the task as done/completed
        - SNOOZE: The user wants to delay the task
        - UPDATE: The user wants to add a comment or update the task
        - VIEW: The user wants to view the task
        - UNKNOWN: Intent is unclear or not related to task management
        
        If SNOOZE, try to determine for how many days (default: 1)
        If UPDATE, extract the comment to add
        
        Return a JSON response with the following format:
        {
            "intent": "COMPLETE|SNOOZE|UPDATE|VIEW|UNKNOWN",
            "days": <number of days if SNOOZE>,
            "comment": "<comment text if UPDATE>"
        }
        """
        
        intent_result = await llm_service.chat_completion(
            messages=[{"role": "user", "content": intent_prompt}],
            model="claude-3-5-sonnet-20240620",
            response_format={"type": "json_object"}
        )
        
        try:
            import json
            intent_data = json.loads(intent_result)
            intent = intent_data.get("intent", "UNKNOWN")
            
            # Process based on intent
            if intent == "COMPLETE":
                # Mark as done
                result = await mark_reminder_done(request, issue_key, current_user, db)
                result["intent"] = "COMPLETE"
                return result
                
            elif intent == "SNOOZE":
                # Snooze the task
                days = intent_data.get("days", 1)
                result = await snooze_reminder(request, issue_key, days, current_user, db)
                result["intent"] = "SNOOZE"
                result["days"] = days
                return result
                
            elif intent == "UPDATE":
                # Add a comment
                comment = intent_data.get("comment", message)
                jira_client.add_comment(issue_key, comment)
                return {
                    "success": True,
                    "intent": "UPDATE",
                    "message": f"Added comment to {issue_key}",
                    "comment": comment
                }
                
            elif intent == "VIEW":
                # Just return success for viewing
                return {
                    "success": True,
                    "intent": "VIEW",
                    "message": f"Viewing issue {issue_key}"
                }
                
            else:
                # Unknown intent
                # Add the message as a comment anyway
                jira_client.add_comment(issue_key, message)
                return {
                    "success": True,
                    "intent": "UNKNOWN",
                    "message": f"Added message as comment to {issue_key}"
                }
                
        except json.JSONDecodeError:
            # If JSON parsing fails, treat as a comment
            jira_client.add_comment(issue_key, message)
            return {
                "success": True,
                "intent": "UNKNOWN",
                "message": f"Added message as comment to {issue_key}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to process reply: {str(e)}"
        }

@router.post("/test")
async def create_test_reminder(
    request: Request,
    message: str = "This is a test reminder",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a test reminder for the current user.
    
    Args:
        message: Test reminder message
        
    Returns:
        The created test reminder
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Create a test notification
    notification = await reminder_service.add_test_notification(
        user_id=current_user["account_id"],
        message=message
    )
    
    return {
        "success": True,
        "reminder": notification
    } 