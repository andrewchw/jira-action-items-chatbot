import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
import requests
from datetime import datetime, timedelta

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class JiraClient:
    """
    Client for interacting with the Jira REST API.
    Handles authentication, sending requests, and error handling.
    """
    
    def __init__(self):
        """Initialize the Jira client with credentials from settings."""
        self.base_url = settings.JIRA_BASE_URL
        self.username = settings.JIRA_USERNAME
        self.api_token = settings.JIRA_API_TOKEN
        
        if not self.base_url or not self.username or not self.api_token:
            logger.warning("Jira credentials not set. Jira functionality will be limited.")
        
        # Default headers for all requests
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Initialize retry settings
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds
        
        logger.info(f"Initialized Jira client for {self.base_url}")
    
    def get_auth(self):
        """Return the authentication tuple for Jira requests."""
        return (self.username, self.api_token)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the Jira API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (will be appended to base_url)
            data: JSON body data for POST/PUT requests
            params: URL parameters for GET requests
            
        Returns:
            Response from the API
        """
        url = f"{self.base_url}{endpoint}"
        
        # Convert data to JSON if present
        json_data = json.dumps(data) if data else None
        
        # Make the request with basic auth
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.get_auth(),
                headers=self.headers,
                params=params,
                data=json_data
            )
            
            # Raise an exception for HTTP errors
            response.raise_for_status()
            
            # Return the JSON response if content exists
            if response.text:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Jira API: {str(e)}")
            raise
    
    def search_issues(self, jql: str, fields: Optional[List[str]] = None, 
                     max_results: int = 50, start_at: int = 0) -> Dict:
        """
        Search for issues using JQL (Jira Query Language).
        
        Args:
            jql: JQL query string
            fields: List of fields to return (default: all)
            max_results: Maximum number of results to return
            start_at: Index to start from for pagination
            
        Returns:
            Response containing matched issues
        """
        endpoint = "/rest/api/2/search"
        
        # Build the request body
        data = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results
        }
        
        # Add fields if specified
        if fields:
            data["fields"] = fields
        
        return self._make_request("POST", endpoint, data=data)
    
    def get_issue(self, issue_key: str, fields: Optional[List[str]] = None) -> Dict:
        """
        Get details for a specific issue.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            fields: List of fields to return (default: all)
            
        Returns:
            Issue details
        """
        endpoint = f"/rest/api/2/issue/{issue_key}"
        
        # Add fields as parameters if specified
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        return self._make_request("GET", endpoint, params=params)
    
    def create_issue(self, project_key: str, issue_type: str, summary: str, 
                    description: Optional[str] = None, 
                    additional_fields: Optional[Dict] = None) -> Dict:
        """
        Create a new issue in Jira.
        
        Args:
            project_key: Project key (e.g., 'PROJECT')
            issue_type: Issue type (e.g., 'Task', 'Bug')
            summary: Issue summary/title
            description: Issue description
            additional_fields: Additional fields to set on the issue
            
        Returns:
            Created issue details
        """
        endpoint = "/rest/api/2/issue"
        
        # Build the issue data
        data = {
            "fields": {
                "project": {
                    "key": project_key
                },
                "issuetype": {
                    "name": issue_type
                },
                "summary": summary
            }
        }
        
        # Add description if provided
        if description:
            data["fields"]["description"] = description
        
        # Add any additional fields
        if additional_fields:
            data["fields"].update(additional_fields)
        
        return self._make_request("POST", endpoint, data=data)
    
    def update_issue(self, issue_key: str, fields: Dict) -> Dict:
        """
        Update an existing issue in Jira.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            fields: Fields to update
            
        Returns:
            Empty dict if successful
        """
        endpoint = f"/rest/api/2/issue/{issue_key}"
        
        # Build the update data
        data = {
            "fields": fields
        }
        
        return self._make_request("PUT", endpoint, data=data)
    
    def add_comment(self, issue_key: str, comment: str, visibility: Optional[Dict] = None) -> Dict:
        """
        Add a comment to an issue.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            comment: The comment text
            visibility: Optional dict defining comment visibility (e.g., {"type": "role", "value": "Administrators"})
            
        Returns:
            Created comment details
        """
        endpoint = f"/rest/api/2/issue/{issue_key}/comment"
        
        # Build the comment data
        data = {
            "body": comment
        }
        
        # Add visibility if provided
        if visibility:
            data["visibility"] = visibility
        
        return self._make_request("POST", endpoint, data=data)
    
    def get_issue_transitions(self, issue_key: str) -> Dict:
        """
        Get available transitions for an issue.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            
        Returns:
            List of available transitions
        """
        endpoint = f"/rest/api/2/issue/{issue_key}/transitions"
        
        return self._make_request("GET", endpoint)
    
    def transition_issue(self, issue_key: str, transition_id: str, 
                        comment: Optional[str] = None, 
                        fields: Optional[Dict] = None) -> Dict:
        """
        Transition an issue to a new status.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            transition_id: ID of the transition to perform
            comment: Optional comment to add with the transition
            fields: Optional fields to update during the transition
            
        Returns:
            Empty dict if successful
        """
        endpoint = f"/rest/api/2/issue/{issue_key}/transitions"
        
        # Build the transition data
        data = {
            "transition": {
                "id": transition_id
            }
        }
        
        # Add comment if provided
        if comment:
            data["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": comment
                        }
                    }
                ]
            }
        
        # Add fields if provided
        if fields:
            data["fields"] = fields
        
        return self._make_request("POST", endpoint, data=data)
    
    def get_projects(self) -> List[Dict]:
        """
        Get all projects.
        
        Returns:
            List of projects
        """
        endpoint = "/rest/api/2/project"
        
        return self._make_request("GET", endpoint)
    
    def get_project(self, project_key: str) -> Dict:
        """
        Get details for a specific project.
        
        Args:
            project_key: The project key (e.g., 'PROJECT')
            
        Returns:
            Project details
        """
        endpoint = f"/rest/api/2/project/{project_key}"
        
        return self._make_request("GET", endpoint)
    
    def get_issue_types(self) -> List[Dict]:
        """
        Get all issue types.
        
        Returns:
            List of issue types
        """
        endpoint = "/rest/api/2/issuetype"
        
        return self._make_request("GET", endpoint)
    
    def assign_issue(self, issue_key: str, assignee: Optional[str] = None) -> Dict:
        """
        Assign an issue to a user.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            assignee: Username to assign to, or None to unassign
            
        Returns:
            Empty dict if successful
        """
        endpoint = f"/rest/api/2/issue/{issue_key}/assignee"
        
        # Build the assignee data
        data = {
            "name": assignee
        }
        
        return self._make_request("PUT", endpoint, data=data)
    
    def get_user(self, username: str) -> Dict:
        """
        Get details for a specific user.
        
        Args:
            username: The username
            
        Returns:
            User details
        """
        endpoint = f"/rest/api/2/user"
        params = {"username": username}
        
        return self._make_request("GET", endpoint, params=params)
    
    def search_users(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search for users.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of matched users
        """
        endpoint = f"/rest/api/2/user/search"
        params = {
            "username": query,
            "maxResults": max_results
        }
        
        return self._make_request("GET", endpoint, params=params) 