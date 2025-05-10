"""
Reminder system service for sending browser notifications based on Jira due dates.
Implements scheduled polling of Jira for upcoming tasks and stores pending notifications.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy.orm import Session

from app.services.jira import JiraClient
from app.core.config import settings
from app.models.database import get_db, UserConfig

# Configure logging
logger = logging.getLogger(__name__)

class ReminderService:
    """
    Service for scheduling and managing reminders based on Jira due dates.
    """
    
    def __init__(self):
        """Initialize the reminder service with a scheduler."""
        # Initialize scheduler with SQLAlchemy job store for persistence
        self.scheduler = None
        self.notifications_queue = {}  # User ID -> List of notifications
        self.initialized = False
        logger.info("Reminder service initialized")
    
    async def start(self):
        """Start the reminder service and scheduler."""
        if self.initialized:
            logger.warning("Reminder service already started")
            return

        # Create scheduler with SQLAlchemy job store
        jobstore = SQLAlchemyJobStore(url=settings.DATABASE_URL)
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': jobstore},
            job_defaults={'misfire_grace_time': 30}
        )
        
        # Schedule the job to run every 15 minutes
        # Define check_due_tasks as a static function to avoid scheduler serialization issues
        async def scheduled_check_due_tasks():
            """Run check_due_tasks without referencing the scheduler instance"""
            await self.check_due_tasks()
            
        self.scheduler.add_job(
            scheduled_check_due_tasks,
            trigger=IntervalTrigger(minutes=15),
            id='check_due_tasks',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.initialized = True
        logger.info("Reminder service scheduler started")
    
    async def stop(self):
        """Stop the reminder service and scheduler."""
        if self.scheduler and self.initialized:
            self.scheduler.shutdown()
            self.initialized = False
            logger.info("Reminder service scheduler stopped")
    
    async def check_due_tasks(self):
        """
        Check for due tasks in Jira and queue notifications.
        This job runs on the scheduler's interval.
        """
        logger.info("Checking for due Jira tasks...")
        try:
            # Get all users with Jira access tokens
            db = next(get_db())
            users = db.query(UserConfig).filter(
                UserConfig.jira_access_token.isnot(None)
            ).all()
            
            for user in users:
                await self.check_user_tasks(db, user)
            
            logger.info(f"Due task check completed for {len(users)} users")
        except Exception as e:
            logger.error(f"Error checking due tasks: {e}")
    
    async def check_user_tasks(self, db: Session, user: UserConfig):
        """
        Check due tasks for a specific user and queue notifications.
        
        Args:
            db: Database session
            user: User configuration with Jira tokens
        """
        try:
            # Skip users without access token
            if not user.jira_access_token:
                return
            
            # Initialize Jira client with OAuth for this user
            jira_client = JiraClient(use_oauth=True, user_id=user.user_id)
            jira_client.access_token = user.jira_access_token
            
            # Check if token is valid
            if not jira_client.validate_token():
                logger.warning(f"Invalid Jira token for user {user.user_id}, skipping")
                return
            
            # Current date for JQL queries
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            
            # Query tasks due today
            due_today = jira_client.search_issues(
                jql=f'assignee = currentUser() AND duedate = "{today}" AND resolution = Unresolved ORDER BY priority DESC',
                fields=["summary", "priority", "status", "duedate"]
            )
            
            # Query tasks due tomorrow
            due_tomorrow = jira_client.search_issues(
                jql=f'assignee = currentUser() AND duedate = "{tomorrow}" AND resolution = Unresolved ORDER BY priority DESC',
                fields=["summary", "priority", "status", "duedate"]
            )
            
            # Query tasks due within a week (excluding today and tomorrow)
            due_soon = jira_client.search_issues(
                jql=f'assignee = currentUser() AND duedate > "{tomorrow}" AND duedate <= "{next_week}" AND resolution = Unresolved ORDER BY priority DESC',
                fields=["summary", "priority", "status", "duedate"]
            )
            
            # Process notifications for each time frame
            notifications = []
            
            # Today's tasks are highest priority
            if "issues" in due_today and due_today["issues"]:
                for issue in due_today["issues"]:
                    notifications.append({
                        "key": issue["key"],
                        "title": issue["fields"]["summary"],
                        "priority": self._get_priority_level(issue),
                        "message": f"Task {issue['key']} is due TODAY: {issue['fields']['summary']}",
                        "due_date": issue["fields"]["duedate"],
                        "status": issue["fields"]["status"]["name"],
                        "urgency": "high",
                        "actions": ["Done", "View", "Snooze"],
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Tomorrow's tasks are medium priority
            if "issues" in due_tomorrow and due_tomorrow["issues"]:
                for issue in due_tomorrow["issues"]:
                    notifications.append({
                        "key": issue["key"],
                        "title": issue["fields"]["summary"],
                        "priority": self._get_priority_level(issue),
                        "message": f"Task {issue['key']} is due TOMORROW: {issue['fields']['summary']}",
                        "due_date": issue["fields"]["duedate"],
                        "status": issue["fields"]["status"]["name"],
                        "urgency": "medium",
                        "actions": ["View", "Snooze"],
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Tasks due soon are low priority
            if "issues" in due_soon and due_soon["issues"]:
                for issue in due_soon["issues"]:
                    due_date = datetime.strptime(issue["fields"]["duedate"], "%Y-%m-%d")
                    days_until_due = (due_date - datetime.now()).days
                    
                    notifications.append({
                        "key": issue["key"],
                        "title": issue["fields"]["summary"],
                        "priority": self._get_priority_level(issue),
                        "message": f"Task {issue['key']} is due in {days_until_due} days: {issue['fields']['summary']}",
                        "due_date": issue["fields"]["duedate"],
                        "status": issue["fields"]["status"]["name"],
                        "urgency": "low",
                        "actions": ["View"],
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Store notifications for this user
            if notifications:
                self.notifications_queue[user.user_id] = notifications
                logger.info(f"Queued {len(notifications)} notifications for user {user.user_id}")
            
        except Exception as e:
            logger.error(f"Error checking tasks for user {user.user_id}: {e}")
    
    def _get_priority_level(self, issue: Dict[str, Any]) -> str:
        """Extract priority level from Jira issue."""
        try:
            if "fields" in issue and "priority" in issue["fields"] and issue["fields"]["priority"]:
                return issue["fields"]["priority"]["name"]
            return "Medium"  # Default priority
        except Exception:
            return "Medium"
    
    async def get_pending_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get pending notifications for a user and clear the queue.
        
        Args:
            user_id: User ID to get notifications for
            
        Returns:
            List of notification objects
        """
        if user_id not in self.notifications_queue:
            return []
        
        # Get notifications
        notifications = self.notifications_queue[user_id]
        
        # Clear queue after retrieval
        self.notifications_queue[user_id] = []
        
        return notifications
    
    async def add_test_notification(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Add a test notification for a user.
        
        Args:
            user_id: User ID to add notification for
            message: Notification message
            
        Returns:
            The created notification
        """
        # Create test notification
        notification = {
            "key": "TEST-123",
            "title": "Test Notification",
            "priority": "Medium",
            "message": message,
            "due_date": datetime.now().isoformat(),
            "status": "Open",
            "urgency": "medium",
            "actions": ["Done", "View", "Snooze"],
            "timestamp": datetime.now().isoformat(),
            "is_test": True
        }
        
        # Initialize queue for user if needed
        if user_id not in self.notifications_queue:
            self.notifications_queue[user_id] = []
        
        # Add notification to queue
        self.notifications_queue[user_id].append(notification)
        
        return notification

# Create a singleton instance
reminder_service = ReminderService() 