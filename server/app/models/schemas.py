from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class ChatMessage(BaseModel):
    """
    Schema for chat messages sent from the extension to the API.
    """
    text: str = Field(..., description="The message text content")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    context: Optional[Dict] = Field(None, description="Additional context data")

class ChatResponse(BaseModel):
    """
    Schema for chat responses sent from the API to the extension.
    """
    response: str = Field(..., description="The response text content")
    actions: Optional[List[Dict]] = Field(None, description="Suggested actions based on response")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class TaskStatus(str, Enum):
    """
    Enum for Jira task statuses.
    """
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    BLOCKED = "Blocked"

class JiraTask(BaseModel):
    """
    Schema for Jira tasks.
    """
    id: str = Field(..., description="Jira issue ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: TaskStatus = Field(..., description="Current task status")
    assignee: Optional[str] = Field(None, description="Assigned user")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    
class TaskList(BaseModel):
    """
    Schema for lists of Jira tasks.
    """
    tasks: List[JiraTask] = Field(..., description="List of Jira tasks")
    total: int = Field(..., description="Total number of tasks")

class Reminder(BaseModel):
    """
    Schema for task reminders.
    """
    task_id: str = Field(..., description="Associated Jira task ID")
    reminder_time: datetime = Field(..., description="When to send the reminder")
    message: Optional[str] = Field(None, description="Custom reminder message")
    is_recurring: bool = Field(False, description="Whether the reminder recurs")
    
class ReminderResponse(BaseModel):
    """
    Schema for reminder actions from notification responses.
    """
    task_id: str = Field(..., description="Associated Jira task ID")
    action: str = Field(..., description="User action (e.g., 'done', 'remind_later')")
    notes: Optional[str] = Field(None, description="Optional notes from user")
    
class ErrorResponse(BaseModel):
    """
    Schema for API error responses.
    """
    detail: str = Field(..., description="Error detail message")
    code: Optional[int] = Field(None, description="Error code") 