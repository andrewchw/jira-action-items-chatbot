import os
import logging
import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Union, Tuple
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db, JiraCache, update_jira_cache, get_or_create_user_config, UserConfig, bulk_update_jira_users, get_jira_user_by_name, update_jira_user_cache

# Configure logging
logger = logging.getLogger(__name__)

class JiraClient:
    """
    Client for interacting with the Jira REST API.
    Handles authentication, sending requests, and error handling.
    """
    
    def __init__(self, use_oauth=False, user_id=None):
        """
        Initialize the Jira client with credentials from settings.
        
        Args:
            use_oauth: Whether to use OAuth 2.0 authentication instead of basic auth
            user_id: User ID for OAuth authentication (required if use_oauth is True)
        """
        self.base_url = settings.JIRA_URL
        self.username = settings.JIRA_USERNAME
        self.api_token = settings.JIRA_API_TOKEN
        
        # OAuth settings
        self.use_oauth = use_oauth
        self.user_id = user_id
        self.access_token = None
        
        # Validate base URL
        if not self.base_url:
            logger.error("Jira URL not set. Please set JIRA_URL in your environment variables.")
            self.base_url = "https://your-domain.atlassian.net"  # Fallback URL
        
        # Check if URL has common format issues and try to fix
        if not self.base_url.startswith('http'):
            logger.warning(f"Jira URL does not start with http/https, prepending https://: {self.base_url}")
            self.base_url = f"https://{self.base_url}"
            
        # Remove trailing slash if present
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
            
        # Validate OAuth settings
        if use_oauth and not user_id:
            logger.warning("User ID not provided for OAuth authentication. Falling back to basic auth.")
            self.use_oauth = False
            
        # Validate basic auth credentials
        if not use_oauth:
            if not self.username:
                logger.error("Jira username not set. Please set JIRA_USERNAME in your environment variables.")
            if not self.api_token:
                logger.error("Jira API token not set. Please set JIRA_API_TOKEN in your environment variables.")
                
            if not self.username or not self.api_token:
                logger.warning("Jira basic auth credentials incomplete. Some functionality will be unavailable.")
        
        # Log initialization
        auth_method = "OAuth" if self.use_oauth else "Basic Auth"
        logger.info(f"Initializing Jira client for {self.base_url} using {auth_method}")
          # Default headers for all requests
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Initialize retry settings
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds
        
        # Cache settings
        self.default_cache_ttl = 15  # Default cache TTL in minutes
        
        # Determine if this is a Jira Cloud instance (vs. Server/DC)
        self.is_cloud = ".atlassian.net" in self.base_url.lower()
    
    def get_auth(self):
        """
        Return the authentication tuple for Jira requests.
        
        Returns:
            For basic auth: tuple with (username, api_token)
            For OAuth: None, as the token is passed in headers
        """
        if not self.use_oauth:
            return (self.username, self.api_token)
        return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to the Jira API.
        
        Returns:
            Tuple with (success: bool, message: str)
        """
        try:
            if not self.base_url or not self.username or not self.api_token:
                return False, "Jira credentials not set. Please check your .env file."
            
            # Try to get the current user
            result = self.get_myself()
            
            if result and "displayName" in result:
                return True, f"Connection successful! Connected as: {result['displayName']}"
            else:
                return False, "Connection failed. API responded but user information is missing."
        
        except requests.exceptions.ConnectionError:
            return False, f"Connection error. Could not connect to {self.base_url}"
        except requests.exceptions.HTTPError as e:
            return False, f"HTTP error: {str(e)}"
        except requests.exceptions.Timeout:
            return False, "Connection timed out. Please check your network."
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unknown error: {str(e)}"
    
    def _generate_cache_key(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> str:
        """
        Generate a cache key for a Jira API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: URL parameters
            data: Request data
            
        Returns:
            MD5 hash of the request parameters as a string
        """
        # Create a string representation of the request
        key_parts = [method.upper(), endpoint]
        
        if params:
            # Sort params to ensure consistent key generation
            key_parts.append(json.dumps(params, sort_keys=True))
        
        if data:
            # Sort data to ensure consistent key generation
            key_parts.append(json.dumps(data, sort_keys=True))
        
        # Join parts and create MD5 hash
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _check_jira_cache(self, cache_key: str, max_age_minutes: int = 15) -> Optional[Dict]:
        """
        Check if a cached response exists and is still valid.
        
        Args:
            cache_key: Cache key to check
            max_age_minutes: Maximum age of the cache entry in minutes
            
        Returns:
            Cached response as dictionary or None if not found or expired
        """
        try:
            # This would be replaced with actual database access in a real implementation
            db = next(get_db())
            max_age = datetime.utcnow() - timedelta(minutes=max_age_minutes)
            
            # Query the database for the cache entry
            cache_entry = db.query(JiraCache).filter(
                JiraCache.issue_key == cache_key,
                JiraCache.last_updated > max_age
            ).first()
            
            if cache_entry and cache_entry.raw_data:
                return json.loads(cache_entry.raw_data)
            
            return None
        except Exception as e:
            logger.error(f"Error checking Jira cache: {str(e)}")
            return None
    
    def _save_to_jira_cache(self, cache_key: str, data: Dict) -> None:
        """
        Save a response to the cache.
        
        Args:
            cache_key: Cache key
            data: Response data to cache
        """
        try:
            # This would be replaced with actual database access in a real implementation
            db = next(get_db())
            
            # Extract key fields for the cache entry
            issue_data = {
                "title": self._extract_title(data),
                "description": self._extract_description(data),
                "status": self._extract_status(data),
                "assignee": self._extract_assignee(data),
                "due_date": self._extract_due_date(data),
                "raw_data": json.dumps(data)
            }
            
            # Update or create the cache entry
            update_jira_cache(db, cache_key, issue_data)
            
        except Exception as e:
            logger.error(f"Error saving to Jira cache: {str(e)}")
    
    def _extract_title(self, data: Dict) -> str:
        """Extract title from Jira response data"""
        try:
            if "fields" in data and "summary" in data["fields"]:
                return data["fields"]["summary"]
            return ""
        except Exception:
            return ""
    
    def _extract_description(self, data: Dict) -> str:
        """Extract description from Jira response data"""
        try:
            if "fields" in data and "description" in data["fields"]:
                return data["fields"]["description"]
            return ""
        except Exception:
            return ""
    
    def _extract_status(self, data: Dict) -> str:
        """Extract status from Jira response data"""
        try:
            if "fields" in data and "status" in data["fields"] and "name" in data["fields"]["status"]:
                return data["fields"]["status"]["name"]
            return ""
        except Exception:
            return ""
    
    def _extract_assignee(self, data: Dict) -> str:
        """Extract assignee from Jira response data"""
        try:
            if "fields" in data and "assignee" in data["fields"] and data["fields"]["assignee"]:
                return data["fields"]["assignee"]["displayName"]
            return ""
        except Exception:
            return ""
    
    def _extract_due_date(self, data: Dict) -> Optional[datetime]:
        """Extract due date from Jira response data"""
        try:
            if "fields" in data and "duedate" in data["fields"] and data["fields"]["duedate"]:
                return datetime.strptime(data["fields"]["duedate"], "%Y-%m-%d")
            return None
        except Exception:
            return None
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None,
                     use_cache: bool = True, cache_ttl: int = None) -> Dict:
        """
        Make a request to the Jira API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in minutes
            
        Returns:
            Response data
        """
        # Generate cache key if using cache
        cache_key = None
        if use_cache and method.upper() == "GET":
            cache_key = self._generate_cache_key(method, endpoint, params, data)
            
            # Check cache
            cached_data = self._check_jira_cache(cache_key, cache_ttl or 15)
            if cached_data:
                logger.debug(f"Using cached response for {method} {endpoint}")
                return cached_data
        
        # Construct URL
        url = f"{self.base_url}{endpoint}"
        
        # Prepare request
        auth = self.get_auth()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Log auth type
        if isinstance(auth, tuple):
            logger.debug(f"Using Basic authentication for Jira API request with username: {auth[0]}")
        else:
            logger.debug("Using OAuth authentication for Jira API request")
        
        # Log request details for debugging
        if data:
            logger.debug(f"Request data: {json.dumps(data)} ")
        
        logger.info(f"Making Jira API request: {method} {url}")
        
        # Make request
        try:
            if method.upper() == "GET":
                response = requests.get(url, auth=auth, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, auth=auth, headers=headers, params=params, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, auth=auth, headers=headers, params=params, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, auth=auth, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Log response status
            logger.debug(f"Jira API response status: {response.status_code}")
            logger.debug(f"Jira API response headers: {response.headers}")
            
            # Check for errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    # Handle both errorMessages array and errors object
                    if "errorMessages" in error_data and error_data["errorMessages"]:
                        error_message = error_data["errorMessages"][0]
                    elif "errors" in error_data and error_data["errors"]:
                        # For structured error objects, format them
                        error_parts = []
                        for field, msg in error_data["errors"].items():
                            error_parts.append(f"{field}: {msg}")
                            
                            # Special handling for specific Jira field restrictions
                            # Log extra details for common field restriction errors
                            if "cannot be set" in str(msg) and field == "reporter":
                                logger.warning(f"The Jira instance does not allow setting the reporter field manually. This is common in cloud instances.")
                            
                            # Additional logging for assignee field errors
                            if field == "assignee":
                                logger.error(f"Assignee field error: {msg}")
                                # Print the request data to help debug
                                if data and "fields" in data and "assignee" in data["fields"]:
                                    logger.error(f"Assignee data sent: {json.dumps(data['fields']['assignee'])}")
                                
                        error_message = ", ".join(error_parts)
                    else:
                        error_message = f"HTTP error {response.status_code}"
                        
                    logger.error(f"Jira API error: {response.status_code} - {json.dumps(error_data)}")
                    raise ValueError(error_message)
                except ValueError as ve:
                    # Re-raise the formatted error
                    raise ve
                except Exception as e:
                    # Handle JSON parsing errors
                    logger.error(f"Error parsing Jira API error response: {str(e)}")
                    raise ValueError(f"HTTP error {response.status_code}: {response.text}")
            
            # Parse response
            if response.content:
                response_data = response.json()
                
                # Cache response if appropriate
                if cache_key and method.upper() == "GET":
                    self._save_to_jira_cache(cache_key, response_data)
                
                return response_data
            else:
                return {"success": True}
            
        except ValueError as e:
            # Re-raise value errors (validation errors)
            raise
        except Exception as e:
            # Handle other errors
            logger.error(f"Error making Jira API request: {str(e)}")
            raise ValueError(f"Unexpected error: {str(e)}")
    
    def search_issues(self, jql: str, fields: Optional[List[str]] = None, 
                     max_results: int = 50, start_at: int = 0) -> Dict:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            fields: List of fields to retrieve
            max_results: Maximum number of results to return
            start_at: Start index of results
            
        Returns:
            Search results
        """
        endpoint = "/rest/api/3/search"
        
        # Create params
        params = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start_at
        }
        
        # Add fields if specified
        if fields:
            params["fields"] = ",".join(fields)
        
        return self._make_request("GET", endpoint, params=params)
    
    def get_issue(self, issue_key: str, fields: Optional[List[str]] = None) -> Dict:
        """
        Get issue by key.
        
        Args:
            issue_key: Issue key (e.g. PROJECT-123)
            fields: List of fields to retrieve
            
        Returns:
            Issue data
        """
        endpoint = f"/rest/api/3/issue/{issue_key}"
        
        # Create params
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        return self._make_request("GET", endpoint, params=params)
    
    def create_issue(self, project_key: str, summary: str, issue_type: str = "Task",
                 description: str = "", additional_fields: Dict = None) -> Dict:
        """
        Create a new issue.
        
        Args:
            project_key: Project key (e.g. PROJECT)
            summary: Issue summary
            issue_type: Issue type (e.g. Task, Bug, etc.)
            description: Issue description
            additional_fields: Additional fields to set
            
        Returns:
            Created issue data
        """
        # Set up base fields
        fields = {
                "project": {
                    "key": project_key
                },
            "summary": summary,
                "issuetype": {
                    "name": issue_type
            }
        }        # Try to set reporter to current user if not specified in additional fields
        # Note: Some Jira instances (especially cloud) don't allow manually setting the reporter
        # In those cases, Jira will automatically set the reporter to the API user
        reporter_in_additional = additional_fields and 'reporter' in additional_fields
        
        # Check if we should try to set the reporter field automatically
        # Only do this if:
        # 1. The reporter is not already specified in additional_fields
        # 2. We're not in a Jira Cloud instance (which usually doesn't allow setting reporter)
        #    OR we've specifically checked that this instance supports it
        if not reporter_in_additional and (not self.is_cloud or hasattr(self, '_supports_reporter') and self._supports_reporter):
            try:
                myself = self.get_myself()
                if myself and ('accountId' in myself or 'name' in myself):
                    reporter_field = {}
                    if self.is_cloud and 'accountId' in myself:
                        reporter_field["accountId"] = myself["accountId"]
                    elif 'name' in myself:
                        reporter_field["name"] = myself["name"]
                    
                    if reporter_field:
                        fields["reporter"] = reporter_field
                        logger.info(f"Setting reporter to current user: {myself.get('displayName', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Failed to set reporter to current user: {str(e)}")
        elif reporter_in_additional and self.is_cloud:
            # If the user explicitly specified a reporter but we're in a cloud instance,
            # warn them that it might not work
            logger.warning("Reporter field specified in additional_fields, but Jira Cloud often doesn't allow setting this field")
        
        # Add description if provided - format as Atlassian Document Format (ADF) for API v3
        if description:
            # Create a simple ADF document
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            }
            
        # Add additional fields
        if additional_fields:
            for key, value in additional_fields.items():
                # Handle common fields
                if key == "priority":
                    # Handle priority as string or object
                    if isinstance(value, str):
                        fields["priority"] = {"name": value}
                    else:
                        fields["priority"] = value                
                elif key == "labels":                    
                    # Handle labels as list or string
                    if isinstance(value, str):
                        fields["labels"] = [v.strip() for v in value.split(",")]
                    else:
                        fields["labels"] = value                
                elif key == "assignee":
                    # Handle assignee as string or object
                    if isinstance(value, str):
                        # Check if this looks like an email (contains @)
                        if '@' in value:
                            fields["assignee"] = {"emailAddress": value}
                            logger.info(f"Using email address for assignee: {value}")
                        # Check if it's an account ID (looks like a UUID with standard format)
                        # UUID standard format: 8-4-4-4-12 hex digits (36 chars including hyphens)
                        elif len(value) > 20 and '-' in value and value.count('-') >= 4:
                            fields["assignee"] = {"accountId": value}
                            logger.info(f"Using account ID for assignee: {value}")
                        else:
                            # For Jira Cloud instances, must have a valid accountId UUID format
                            if self.is_cloud:
                                # Try to find a valid account ID for this username/string
                                account_id = self.find_user_account_id(value)
                                if account_id:
                                    fields["assignee"] = {"accountId": account_id}
                                    logger.info(f"Translated assignee '{value}' to accountId: {account_id}")
                                else:                                    # This will fail because Jira Cloud requires accountId in valid format
                                    # Log a warning but continue (the API will return a proper error)
                                    logger.warning(f"INVALID ASSIGNEE FORMAT: '{value}' is not a valid accountId for Jira Cloud and could not be resolved.")
                                    logger.warning("Skipping assignee field as it would fail validation.")
                                    # Skip adding this field rather than sending an invalid format
                                    continue
                            else:
                                # For server/DC instances, username is acceptable
                                fields["assignee"] = {"name": value}
                                logger.debug(f"Setting assignee with username: {value}")
                    else:
                        # Handle object format (should be pre-formatted correctly)
                        fields["assignee"] = value
                elif key == "reporter":
                    # Note: Some Jira instances don't allow setting reporter directly
                    # We'll include it in the request, but it might be ignored
                    logger.info(f"Attempting to set reporter explicitly (may not be supported by all Jira instances)")
                    if isinstance(value, str):
                        # Check if this looks like an email (contains @)
                        if '@' in value:
                            fields["reporter"] = {"emailAddress": value}
                        # Check if it's an account ID (looks like a UUID)
                        elif len(value) > 10 and '-' in value:
                            fields["reporter"] = {"accountId": value}
                        else:
                            # First try accountId, then name - depends on Jira version
                            fields["reporter"] = {"accountId": value} if self.is_cloud else {"name": value}
                    else:
                        fields["reporter"] = value
                elif key == "due_date":
                    # Handle due date - correct field name for Jira API is 'duedate'
                    fields["duedate"] = value
                else:
                    # Add field directly
                    fields[key] = value
        
        # Create request data
        data = {
            "fields": fields
        }
        
        # Make request
        return self._make_request(
            "POST", 
            endpoint="/rest/api/3/issue",
            data=data
        )
    
    def update_issue(self, issue_key: str, fields: Dict) -> Dict:
        """
        Update an existing issue.
        
        Args:
            issue_key: Issue key (e.g. PROJECT-123)
            fields: Fields to update
            
        Returns:
            Response from the API
        """
        endpoint = f"/rest/api/3/issue/{issue_key}"
        
        # Create request data
        data = {
            "fields": fields
        }
        
        # Make request
        return self._make_request("PUT", endpoint, data=data)
    
    def add_comment(self, issue_key: str, comment: str, visibility: Optional[Dict] = None) -> Dict:
        """
        Add a comment to an issue.
        
        Args:
            issue_key: Issue key (e.g. PROJECT-123)
            comment: Comment text
            visibility: Visibility restrictions (e.g. {"type": "role", "value": "Administrators"})
            
        Returns:
            Response from the API
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/comment"
        
        # Create comment data
        data = {
            "body": comment
        }
        
        # Add visibility if specified
        if visibility:
            data["visibility"] = visibility
        
        # Make request
        return self._make_request("POST", endpoint, data=data)
    
    def get_issue_transitions(self, issue_key: str) -> Dict:
        """
        Get available transitions for an issue.
        
        Args:
            issue_key: Issue key (e.g. PROJECT-123)
            
        Returns:
            Available transitions
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/transitions"
        
        return self._make_request("GET", endpoint)
    
    def transition_issue(self, issue_key: str, transition_id: str, 
                        comment: Optional[str] = None, 
                        fields: Optional[Dict] = None) -> Dict:
        """
        Transition an issue to a new status.
        
        Args:
            issue_key: Issue key (e.g. PROJECT-123)
            transition_id: Transition ID
            comment: Comment to add
            fields: Fields to update during transition
            
        Returns:
            Response from the API
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/transitions"
        
        # Create transition data
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
        
        # Make request
        return self._make_request("POST", endpoint, data=data)
    
    def get_projects(self) -> List[Dict]:
        """
        Get all projects.
        
        Returns:
            List of projects
        """
        endpoint = "/rest/api/3/project"
        
        return self._make_request("GET", endpoint)
    
    def get_project(self, project_key: str) -> Dict:
        """
        Get a specific project.
        
        Args:
            project_key: Project key (e.g. PROJECT)
            
        Returns:
            Project data
        """
        endpoint = f"/rest/api/3/project/{project_key}"
        
        return self._make_request("GET", endpoint)
    
    def get_issue_types(self) -> List[Dict]:
        """
        Get all issue types.
        
        Returns:
            List of issue types
        """
        endpoint = "/rest/api/3/issuetype"
        
        return self._make_request("GET", endpoint)
    
    def assign_issue(self, issue_key: str, assignee: Optional[str] = None) -> Dict:
        """
        Assign an issue to a user.
        
        Args:
            issue_key: Issue key (e.g. PROJECT-123)
            assignee: Username of the assignee, or None to unassign
            
        Returns:
            Response from the API
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/assignee"
        
        # Create assignee data
        data = {}
        if assignee:
            data["name"] = assignee
        
        # Make request
        return self._make_request("PUT", endpoint, data=data)
    
    def get_user(self, username: str) -> Dict:
        """
        Get user information.
        
        Args:
            username: Username
            
        Returns:
            User data
        """
        endpoint = f"/rest/api/3/user"
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
        endpoint = f"/rest/api/3/user/search"
        params = {
            "query": query,
            "maxResults": max_results
        }
        
        return self._make_request("GET", endpoint, params=params)
    
    # New methods for entity mapping and natural language processing
    def map_nl_to_jira_fields(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map natural language entities to Jira fields.
        
        Args:
            entities: Dictionary of entities extracted from natural language
            
        Returns:
            Dictionary of Jira fields
        """
        jira_fields = {}
        # Map common entities to Jira fields
        field_mappings = {
            "summary": ["summary", "title", "subject"],
            "description": ["description", "details", "body"],
            "assignee": ["assignee", "assigned_to", "owner"],
            "reporter": ["reporter", "reported_by", "creator"],
            "priority": ["priority", "importance"],
            "due_date": ["due_date", "deadline", "due"],
            "type": ["type", "issue_type", "ticket_type"],
            "labels": ["labels", "tags"],
            "components": ["components", "parts"],
            "project": ["project", "project_key", "project_name"]
        }
        
        # Process each entity and map to corresponding Jira field
        for jira_field, entity_keys in field_mappings.items():
            for key in entity_keys:
                if key in entities and entities[key]:                    
                    # Special handling for different field types
                    if jira_field == "assignee" or jira_field == "reporter":
                        # Map to correct user structure based on instance type
                        user_value = entities[key]
                        if '@' in user_value:
                            # If it looks like an email, use emailAddress
                            jira_fields[jira_field] = {"emailAddress": user_value}
                        elif self.is_cloud:
                            # For cloud, prefer accountId but fallback to name if it's all we have
                            # The actual accountId resolution happens later in create_jira_issue
                            jira_fields[jira_field] = {"accountId": user_value}
                        else:
                            # For server/DC, use name
                            jira_fields[jira_field] = {"name": user_value}
                    elif jira_field == "priority":
                        # Map priority string to Jira priority structure
                        priority_name = self._map_priority_name(entities[key])
                        jira_fields[jira_field] = {"name": priority_name}
                    elif jira_field == "due_date":
                        # Convert date string to appropriate format
                        jira_fields[jira_field] = self._format_date(entities[key])
                    elif jira_field in ["labels", "components"]:
                        # Handle arrays
                        values = entities[key]
                        if isinstance(values, str):
                            values = [v.strip() for v in values.split(",")]
                        jira_fields[jira_field] = values
                    else:
                        # Direct mapping for other fields
                        jira_fields[jira_field] = entities[key]
                    break
        
        return jira_fields
    
    def _map_priority_name(self, priority_str: str) -> str:
        """
        Map a priority string from natural language to a Jira priority name.
        
        Args:
            priority_str: Priority string from natural language
            
        Returns:
            Jira priority name
        """
        priority_map = {
            "highest": "Highest",
            "high": "High",
            "medium": "Medium",
            "normal": "Medium",
            "low": "Low",
            "lowest": "Lowest",
            "critical": "Highest",
            "major": "High",
            "minor": "Low",
            "trivial": "Lowest",
            "blocker": "Highest",
            "1": "Highest",
            "2": "High",
            "3": "Medium",
            "4": "Low",
            "5": "Lowest"
        }
        
        # Convert to lowercase for case-insensitive matching
        priority_lower = priority_str.lower()
        
        # Return mapped priority or default to "Medium"
        return priority_map.get(priority_lower, "Medium")
    
    def _format_date(self, date_str: str) -> str:
        """
        Format a date string for Jira.
        
        Args:
            date_str: Date string from natural language
            
        Returns:
            Formatted date string (YYYY-MM-DD)
        """
        try:
            # Try to parse the date string using various formats
            formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%d-%m-%Y",
                "%m-%d-%Y",
                "%b %d, %Y",
                "%B %d, %Y",
                "%d %b %Y",
                "%d %B %Y"
            ]
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # If none of the formats match, try a more flexible approach
            import dateparser
            date_obj = dateparser.parse(date_str)
            if date_obj:
                return date_obj.strftime("%Y-%m-%d")
            
            # If all else fails, return the original string
            return date_str
        except Exception as e:
            logger.error(f"Error formatting date: {str(e)}")
            return date_str
    
    def map_jira_to_nl_entities(self, jira_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Jira fields to natural language entities.
        
        Args:
            jira_data: Dictionary of Jira data
            
        Returns:
            Dictionary of natural language entities
        """
        entities = {}
        
        # Extract fields from Jira data
        if "fields" in jira_data:
            fields = jira_data["fields"]
            
            # Map basic fields
            if "summary" in fields:
                entities["title"] = fields["summary"]
            
            if "description" in fields:
                entities["description"] = fields["description"]
            
            if "assignee" in fields and fields["assignee"]:
                entities["assignee"] = fields["assignee"].get("displayName", "")
            
            if "priority" in fields and fields["priority"]:
                entities["priority"] = fields["priority"].get("name", "")
            
            if "duedate" in fields and fields["duedate"]:
                entities["due_date"] = fields["duedate"]
            
            if "issuetype" in fields and fields["issuetype"]:
                entities["type"] = fields["issuetype"].get("name", "")
            
            if "labels" in fields:
                entities["labels"] = fields["labels"]
            
            if "components" in fields:
                entities["components"] = [c.get("name", "") for c in fields["components"]]
            
            if "project" in fields and fields["project"]:
                entities["project"] = fields["project"].get("name", "")
                entities["project_key"] = fields["project"].get("key", "")
            
            # Add key fields
            if "key" in jira_data:
                entities["issue_key"] = jira_data["key"]
        
        return entities
    
    def extract_issue_key_from_text(self, text: str) -> Optional[str]:
        """
        Extract a Jira issue key from text using regex.
        
        Args:
            text: Text to extract issue key from
            
        Returns:
            Extracted issue key or None if not found
        """
        import re
        
        # Regex pattern for Jira issue keys (e.g., PROJECT-123)
        pattern = r'([A-Z][A-Z0-9_]*)-(\d+)'
        
        # Search for the pattern in the text
        match = re.search(pattern, text)
        
        if match:
            return match.group(0)
        
        return None
    
    def extract_project_key_from_text(self, text: str) -> Optional[str]:
        """
        Extract a Jira project key from text using regex.
        
        Args:
            text: Text to extract project key from
            
        Returns:
            Extracted project key or None if not found
        """
        import re
        
        # Regex pattern for Jira project keys (e.g., PROJECT)
        pattern = r'\b([A-Z][A-Z0-9_]{1,10})\b'
        
        # Search for the pattern in the text
        matches = re.findall(pattern, text)
        
        if matches:
            # Get project keys from the API to validate
            projects = self.get_projects()
            project_keys = [p.get('key') for p in projects]
            
            # Return the first match that is a valid project key
            for match in matches:
                if match in project_keys:
                    return match
        
        return None
    
    def rotate_api_token(self, new_token: str) -> bool:
        """
        Rotate the API token used for authentication.
        
        Args:
            new_token: New API token
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the in-memory token
            self.api_token = new_token
            
            # Store the new token securely in the database
            db = next(get_db())
            
            # Get or create user config for the current user
            user_config = get_or_create_user_config(db, self.username)
            
            # Update the token
            user_config.jira_token = new_token
            db.commit()
            
            logger.info(f"Rotated API token for user {self.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate API token: {str(e)}")
            return False
    
    def load_token_from_database(self) -> bool:
        """
        Load the API token from the database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            db = next(get_db())
            
            # Get user config for the current user
            user_config = db.query(UserConfig).filter(UserConfig.user_id == self.username).first()
            
            if user_config and user_config.jira_token:
                # Update the in-memory token
                self.api_token = user_config.jira_token
                logger.info(f"Loaded API token for user {self.username} from database")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to load API token from database: {str(e)}")
            return False
    
    def validate_token(self) -> bool:
        """
        Validate the current API token by making a test request.
        
        Returns:
            True if the token is valid, False otherwise
        """
        try:
            # Make a simple request to check if the token is valid
            self.get_myself()
            return True
        except Exception:
            logger.warning(f"API token validation failed for user {self.username}")
            return False
    
    def get_myself(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            User data from Jira
        """
        endpoint = "/rest/api/3/myself"
        
        return self._make_request("GET", endpoint)
    
    def generate_token_hash(self, token: str) -> str:
        """
        Generate a hash of the token for secure storage comparison.
        
        Args:
            token: Token to hash
            
        Returns:
            SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def load_oauth_token(self, db):
        """
        Load OAuth access token from the database for the current user.
        
        Args:
            db: Database session
            
        Returns:
            True if token was loaded successfully, False otherwise
        """
        if not self.use_oauth or not self.user_id:
            return False
            
        try:
            # Query the UserConfig table for this user
            user_config = db.query(UserConfig).filter(UserConfig.user_id == self.user_id).first()
            
            if not user_config or not user_config.jira_access_token:
                logger.warning(f"No OAuth token found for user {self.user_id}")
                return False
                
            # Check if token is expired
            if user_config.jira_token_expires_at and user_config.jira_token_expires_at <= datetime.utcnow():
                logger.info(f"OAuth token for user {self.user_id} is expired. Need to refresh.")
                return False
                
            # Set the access token
            self.access_token = user_config.jira_access_token
            logger.info(f"Loaded OAuth token for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading OAuth token: {str(e)}")
            return False
    
    def sync_users(self, db: Session) -> Dict[str, Any]:
        """
        Sync users from Jira to local database. Uses different methods based on Jira server
        version to accommodate GDPR mode and other limitations.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with results of sync operation
        """
        try:
            users = []
            
            # Try first with /rest/api/3/users/search endpoint (Cloud)
            try:
                # Try using the newer search endpoint with query parameter
                cloud_users = self._make_request(
                    "GET", 
                    "/rest/api/3/user/search", 
                    params={"query": "", "maxResults": 1000}
                )
                
                if isinstance(cloud_users, list):
                    users.extend(cloud_users)
                    logger.info(f"Found {len(cloud_users)} users using cloud search endpoint")
            except Exception as e:
                logger.warning(f"Failed to get users with cloud search endpoint: {str(e)}")
                
                # If the first method fails, try the older endpoint
                try:
                    # Some Jira instances need to use the older /user endpoint
                    standard_users = self._make_request(
                        "GET", 
                        "/rest/api/3/user", 
                        params={"username": "", "maxResults": 1000}
                    )
                    
                    if isinstance(standard_users, list):
                        users.extend(standard_users)
                        logger.info(f"Found {len(standard_users)} users using standard user endpoint")
                except Exception as e2:
                    logger.warning(f"Failed to get users with standard user endpoint: {str(e2)}")
            
            # If both previous methods failed, try getting users from groups
            if not users:
                try:
                    # Get admin groups first
                    admin_groups = self._make_request(
                        "GET", 
                        "/rest/api/3/groups", 
                        params={"maxResults": 100}
                    )
                    
                    # Get users from each group
                    for group in admin_groups.get("groups", []):
                        try:
                            group_users = self._make_request(
                                "GET", 
                                f"/rest/api/3/group/member", 
                                params={"groupname": group["name"], "maxResults": 1000}
                            )
                            
                            if "values" in group_users:
                                users.extend(group_users["values"])
                                logger.info(f"Found {len(group_users['values'])} users in group {group['name']}")
                        except Exception as group_err:
                            logger.warning(f"Failed to get users from group {group['name']}: {str(group_err)}")
                except Exception as group_list_err:
                    logger.warning(f"Failed to get groups: {str(group_list_err)}")
            
            # Last resort - try to get user details from project leads
            if not users:
                try:
                    projects = self._make_request("GET", "/rest/api/3/project")
                    
                    for project in projects:
                        if "lead" in project and project["lead"] not in users:
                            users.append(project["lead"])
                            logger.info(f"Added user from project lead: {project['lead'].get('displayName', 'Unknown')}")
                except Exception as project_err:
                    logger.warning(f"Failed to get project leads: {str(project_err)}")
            
            # Remove duplicates based on accountId or name
            unique_users = []
            unique_ids = set()
            
            for user in users:
                user_id = user.get("accountId") or user.get("name")
                if user_id and user_id not in unique_ids:
                    unique_ids.add(user_id)
                    unique_users.append(user)
            
            # Update user cache in database
            updated_count = bulk_update_jira_users(db, unique_users)
            
            return {
                "success": True,
                "total_users": len(unique_users),
                "updated_users": updated_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing users: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
            
    def supports_reporter_field(self) -> bool:
        """
        Check if the Jira instance supports setting the reporter field.
        This is often restricted in Jira Cloud instances.
        
        Returns:
            True if setting the reporter field is supported, False otherwise
        """
        # First, check if we already know the answer from instance memory
        if hasattr(self, '_supports_reporter'):
            return self._supports_reporter
            
        # Then, check if we have a stored preference in the database
        try:
            db = next(get_db())
            
            # Since this is a per-instance setting, use the base URL as the key
            key = f"jira_reporter_support_{self._generate_cache_key('GET', self.base_url, None, None)}"
            
            # Get user config
            user_id = self.user_id or "default"
            config = db.query(UserConfig).filter(
                UserConfig.user_id == user_id,
                UserConfig.key == key
            ).first()
            
            if config:
                support_value = config.value.lower() == 'true'
                self._supports_reporter = support_value
                logger.info(f"Using stored reporter field support preference: {support_value}")
                return support_value
        except Exception as e:
            logger.debug(f"Could not retrieve reporter field support preference: {str(e)}")
        
        # Most Jira Cloud instances don't allow setting reporter directly via API
        if self.is_cloud:
            try:
                # Try to get field metadata which would indicate if the field is editable
                fields_endpoint = "/rest/api/3/field"
                fields_data = self._make_request("GET", fields_endpoint)
                
                # Look for the reporter field in the returned fields
                reporter_field = next((f for f in fields_data if f.get("name") == "Reporter"), None)
                
                # If the field exists and is not marked as readonly
                if reporter_field and not reporter_field.get("schema", {}).get("readonly", False):
                    logger.info("Jira instance supports setting reporter field")
                    support_value = True
                else:
                    logger.info("Jira instance does not support setting reporter field")
                    support_value = False
                
                # Save this result for future use
                self.set_reporter_field_support(support_value)
                return support_value
            except Exception as e:
                logger.warning(f"Could not determine if reporter field is supported: {str(e)}")
                # Default to false for cloud instances when in doubt
                self.set_reporter_field_support(False)
                return False
        
        # Server/DC instances typically allow setting reporter
        support_value = not self.is_cloud
        self.set_reporter_field_support(support_value)
        return support_value

    def set_reporter_field_support(self, supported: bool = False) -> None:
        """
        Set whether this Jira instance supports setting the reporter field.
        This allows the client to avoid attempting to set the reporter field
        for instances that don't support it.
        
        Args:
            supported: Whether the reporter field is supported
        """
        self._supports_reporter = supported
        
        # Try to store this in user preferences if database is available
        try:
            # Get user settings from database
            db = next(get_db())
            
            # Since this is a per-instance setting, use the base URL as the key
            key = f"jira_reporter_support_{self._generate_cache_key('GET', self.base_url, None, None)}"
            
            # Create or update user config
            user_id = self.user_id or "default"
            config = get_or_create_user_config(db, user_id, key, str(supported).lower())
            
            logger.info(f"Saved reporter field support preference for {self.base_url}: {supported}")
        except Exception as e:
            logger.warning(f"Could not save reporter field support preference: {str(e)}")
            # Still store it in instance memory
            self._supports_reporter = supported    
    
    def find_user_account_id(self, username_or_email: str) -> Optional[str]:
        """
        Find the account ID for a user by their username or email.
        This is particularly important for Jira Cloud where account IDs are required.
        
        Args:
            username_or_email: Username or email of the user
            
        Returns:
            Account ID if found, otherwise None
        """
        try:            # Check if the input already looks like a valid account ID
            # Case 1: Standard UUID format with dashes (8-4-4-4-12 hex digits)
            if (isinstance(username_or_email, str) and 
                len(username_or_email) > 20 and 
                '-' in username_or_email and 
                username_or_email.count('-') >= 4):
                
                # This looks like a valid UUID format account ID
                logger.info(f"Input '{username_or_email}' appears to be a valid UUID format, using directly")
                return username_or_email
                  # Case 2: Atlassian numeric account ID format (often starts with 5)
            elif (isinstance(username_or_email, str) and 
                 len(username_or_email) > 10 and
                 username_or_email.startswith("5") and
                 all(c.isalnum() for c in username_or_email)):
                
                # This is a valid Atlassian numeric account ID
                logger.info(f"Input '{username_or_email}' appears to be a valid numeric Atlassian account ID, using directly")
                return username_or_email
                
            # Case 3: Non-standard Atlassian account ID (alphanumeric but no dashes)
            elif (isinstance(username_or_email, str) and
                 len(username_or_email) > 10 and
                 all(c.isalnum() for c in username_or_email)):
                
                # This might be a valid non-standard Atlassian account ID
                logger.info(f"Input '{username_or_email}' appears to be a valid non-standard format account ID, using directly")
                return username_or_email
                
            # Try to search by query
            logger.info(f"Searching for Jira user account ID with query: {username_or_email}")
            users = self._make_request(
                "GET", 
                "/rest/api/3/user/search", 
                params={"query": username_or_email, "maxResults": 10}
            )
            
            if users and isinstance(users, list):
                logger.info(f"Found {len(users)} users matching '{username_or_email}'")
                # Check for exact or close matches first
                for user in users:
                    # For email matches (most reliable)
                    if "emailAddress" in user and user["emailAddress"] and user["emailAddress"].lower() == username_or_email.lower():
                        logger.info(f"Found exact email match: {user.get('emailAddress')} with accountId: {user.get('accountId')}")
                        return user.get("accountId")
                    
                    # For username matches
                    if "name" in user and user["name"] and user["name"].lower() == username_or_email.lower():
                        logger.info(f"Found exact username match: {user.get('name')} with accountId: {user.get('accountId')}")
                        return user.get("accountId")
                    
                    # For display name matches
                    if "displayName" in user and user["displayName"] and user["displayName"].lower() == username_or_email.lower():
                        logger.info(f"Found exact display name match: {user.get('displayName')} with accountId: {user.get('accountId')}")
                        return user.get("accountId")
                
                # Check for partial matches if no exact match found
                for user in users:
                    # For partial display name matches (case insensitive)
                    if "displayName" in user and user["displayName"] and username_or_email.lower() in user["displayName"].lower():
                        logger.info(f"Found partial display name match: {user.get('displayName')} with accountId: {user.get('accountId')}")
                        return user.get("accountId")
                    
                    # For partial username matches (case insensitive)
                    if "name" in user and user["name"] and username_or_email.lower() in user["name"].lower():
                        logger.info(f"Found partial username match: {user.get('name')} with accountId: {user.get('accountId')}")
                        return user.get("accountId")
                
                # If no specific match found but we have results, return the first account ID
                if len(users) > 0 and "accountId" in users[0]:
                    logger.warning(f"No exact match found for '{username_or_email}', using closest match: {users[0].get('displayName')}")
                    return users[0].get("accountId")
            
            # If direct search didn't work, try user picker API as a fallback
            try:
                logger.info(f"Trying user picker API for '{username_or_email}'")
                picker_results = self._make_request(
                    "GET",
                    "/rest/api/3/user/picker",
                    params={"query": username_or_email, "maxResults": 1}
                )
                
                if picker_results and "users" in picker_results and picker_results["users"]:
                    user = picker_results["users"][0]
                    if "accountId" in user:
                        logger.info(f"Found user via picker API: {user.get('displayName')} with accountId: {user.get('accountId')}")
                        return user.get("accountId")
            except Exception as picker_err:
                logger.warning(f"User picker API attempt failed: {str(picker_err)}")
                
            logger.warning(f"Could not find account ID for '{username_or_email}'")
            return None
            
        except Exception as e:
            logger.error(f"Error finding user account ID for '{username_or_email}': {str(e)}")
            return None

    def get_user(self, username: str) -> Dict:
        """
        Get user information.
        
        Args:
            username: Username
            
        Returns:
            User data
        """
        endpoint = f"/rest/api/3/user"
        params = {"username": username}
        
        return self._make_request("GET", endpoint, params=params)

# Standalone function for creating Jira issues (used by API endpoints)
def create_jira_issue(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Jira issue based on extracted entities.
    
    Args:
        entities: Dictionary of entities extracted from user input
        
    Returns:
        Response from Jira API or error dict
    """
    try:
        # Create a client instance - attempt to use OAuth if user_id is in the entities
        user_id = entities.get("user_id")
        use_oauth = bool(user_id)
        
        # Create client with OAuth if possible
        client = JiraClient(use_oauth=use_oauth, user_id=user_id)
        
        # Log authentication method
        if use_oauth:
            logger.info(f"Creating Jira issue with OAuth authentication for user {user_id}")
            # Try to load OAuth token from database
            db = next(get_db())
            token_loaded = client.load_oauth_token(db)
            
            if not token_loaded:
                logger.warning(f"Failed to load OAuth token for user {user_id}, falling back to basic auth")
                # Force fallback to basic auth - don't use the client's default token
                client = JiraClient(use_oauth=False)
        else:
            logger.info("Creating Jira issue with basic authentication")
        
        # Extract required fields with defaults
        project_key = entities.get("project_key")
        if not project_key:
            # Use default project if not specified
            project_key = settings.DEFAULT_JIRA_PROJECT_KEY
            if not project_key:
                return {"error": "Project key is required but not provided"}
        
        # Handle either summary or title
        summary = entities.get("summary", entities.get("title", ""))
        if not summary:
            return {"error": "Summary or title is required"}
        
        # Get description
        description = entities.get("description", "")
        
        # Get issue type
        issue_type = entities.get("issue_type", "Task")            
        # Validate assignee if provided
        if entities.get("assignee"):
            assignee = entities.get("assignee")
            db = next(get_db())
            
            # First, try to find user in our local cache
            cached_user = get_jira_user_by_name(db, assignee)
            
            if cached_user:
                # We found the user in our local cache
                if client.is_cloud and cached_user.account_id:
                    # For Cloud instances, we must use the account_id
                    entities["assignee"] = cached_user.account_id
                    logger.info(f"Found cached user for assignee '{assignee}': {cached_user.display_name} (using account_id: {cached_user.account_id})")
                else:
                    # For Server/DC instances, use the username
                    entities["assignee"] = cached_user.username
                    logger.info(f"Found cached user for assignee '{assignee}': {cached_user.username}")
            else:
                # We need to validate the assignee against Jira
                # Check if we're in GDPR mode - if so, we may not be able to search for users                
                # try:
                valid_user = False
                  # For Jira Cloud, we need to find the account ID
                if client.is_cloud:                    # First, check if the assignee is already a valid account ID
                    # Case 1: Standard UUID format with dashes
                    if (isinstance(assignee, str) and 
                        len(assignee) > 20 and 
                        '-' in assignee and 
                        assignee.count('-') >= 4):
                        
                        # Already looks like a valid accountId UUID format
                        entities["assignee"] = assignee
                        logger.info(f"Assignee '{assignee}' appears to be in valid UUID format, using directly")
                        valid_user = True                    # Case 2: Atlassian numeric account ID format (often starts with 5)
                    elif (isinstance(assignee, str) and 
                         len(assignee) > 10 and
                         assignee.startswith("5") and
                         all(c.isalnum() for c in assignee)):
                        
                        # This is a valid Atlassian numeric ID format
                        entities["assignee"] = assignee
                        logger.info(f"Assignee '{assignee}' appears to be a valid numeric Atlassian ID, using directly")
                        valid_user = True
                    # Case 3: Non-standard Atlassian account ID (alphanumeric but no dashes)
                    elif (isinstance(assignee, str) and
                         len(assignee) > 10 and
                         all(c.isalnum() for c in assignee)):
                        
                        # This might be a valid non-standard Atlassian account ID
                        entities["assignee"] = assignee
                        logger.info(f"Assignee '{assignee}' appears to be a valid non-standard account ID, using directly")
                        valid_user = True
                    else:
                        # Use our dedicated method to find a user's account ID
                        logger.info(f"Looking up account ID for assignee '{assignee}'")
                        account_id = client.find_user_account_id(assignee)
                        
                        if account_id:
                            # Use the account ID directly
                            entities["assignee"] = account_id
                            logger.info(f"Found Jira Cloud account ID for '{assignee}': {account_id}")
                            valid_user = True
                            
                            # Try to get full user details to cache
                            try:
                                user_details = client._make_request(
                                    "GET",
                                    f"/rest/api/3/user",
                                    params={"accountId": account_id}
                                )
                                if user_details:
                                    update_jira_user_cache(db, user_details)
                                    logger.info(f"Cached user details for '{assignee}' with accountId: {account_id}")
                            except Exception as detail_err:
                                logger.warning(f"Could not fetch full user details for caching: {str(detail_err)}")
                else:
                    # For Server/DC installations, search by name works
                    users = client._make_request(
                        "GET", 
                        "/rest/api/3/user/search", 
                        params={"query": assignee, "maxResults": 10}
                    )                    
                    if users and isinstance(users, list):
                        for user in users:                            
                            if user.get("displayName", "").lower() == assignee.lower() or \
                                user.get("name", "").lower() == assignee.lower() or \
                                user.get("emailAddress", "").lower() == assignee.lower():
                                # For server/DC, use name
                                entities["assignee"] = user.get("name")
                                logger.info(f"Found Jira Server user for assignee '{assignee}': {user.get('name')}")
                                
                                valid_user = True
                                
                                # Also cache this user for future lookups                                update_jira_user_cache(db, user)
                                break
                
                if not valid_user:
                    # Sync users and try again
                    client.sync_users(db)
                    # Try one more time with the local cache
                    cached_user = get_jira_user_by_name(db, assignee)
                    if cached_user:
                        # Use accountId for cloud instances, otherwise username
                        if client.is_cloud and cached_user.account_id:
                            entities["assignee"] = cached_user.account_id
                            logger.info(f"Found user in refreshed cache (using accountId): {cached_user.display_name} ({cached_user.account_id})")
                        else:
                            entities["assignee"] = cached_user.username
                            logger.info(f"Found user in refreshed cache (using username): {cached_user.username}")
                    else:
                        logger.warning(f"Assignee '{assignee}' not found in Jira, may cause creation to fail")
                        # If we're in a cloud instance, this will definitely fail due to account ID requirements
                        if client.is_cloud:
                            return {
                                "error": f"Assignee '{assignee}' not found in Jira Cloud. Please use a valid username, email or account ID."
                            }
                        # For server instances we can try to continue, Jira will validate
        
        # Prepare additional fields
        additional_fields = {}
        for key, value in entities.items():
            # Skip already processed fields
            if key in ["project_key", "summary", "title", "description", "issue_type", "original_query", "user_id"]:
                continue
                
            # Skip empty values
            if value is None or value == "":
                continue
                
            # Add to additional fields
            additional_fields[key] = value
              # Call the Jira API client
        logger.info(f"Creating Jira issue with project_key={project_key}, summary={summary}, issue_type={issue_type}")
          # Add detailed logging for assignee
        if "assignee" in additional_fields:
            assignee_value = additional_fields["assignee"]
            logger.info(f"Using assignee value: {assignee_value}")            
            # Check if we have the correct format for cloud instances
            if client.is_cloud and isinstance(assignee_value, str):                
                if '@' in assignee_value:
                    logger.info("Using email address for assignee in Jira Cloud")
                # Case 1: Standard UUID format with dashes
                elif len(assignee_value) > 20 and '-' in assignee_value and assignee_value.count('-') >= 4:
                    logger.info("Using standard UUID format account ID for assignee in Jira Cloud")
                # Case 2: Numeric Atlassian account ID format
                elif assignee_value.startswith("5") and len(assignee_value) > 10 and all(c.isdigit() for c in assignee_value):
                    logger.info(f"Using numeric Atlassian account ID format for assignee: {assignee_value}")
                # Case 3: Non-standard alphanumeric account ID format without dashes
                elif len(assignee_value) > 10 and all(c.isalnum() for c in assignee_value):
                    logger.info(f"Using non-standard alphanumeric account ID format for assignee: {assignee_value}")
                else:
                    # Try to resolve this string to an account ID
                    logger.warning(f"Attempting to resolve assignee value '{assignee_value}' to a valid account ID")
                    account_id = client.find_user_account_id(assignee_value)
                    
                    if account_id:
                        # Replace with valid account ID
                        additional_fields["assignee"] = account_id
                        logger.info(f"Successfully resolved '{assignee_value}' to account ID: {account_id}")
                    else:
                        logger.error(f"CRITICAL ERROR: Invalid assignee value '{assignee_value}' for Jira Cloud")
                        logger.error("For Jira Cloud, assignee must be an email address or a valid account ID")
                        # For safety, remove the invalid assignee value to prevent API errors
                        logger.warning("Removing invalid assignee to prevent API errors")
                        del additional_fields["assignee"]
        
        result = client.create_issue(
            project_key=project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
            additional_fields=additional_fields
        )
          # Format response to include all important information
        if "key" in result:
            return {
                "success": True,
                "key": result["key"],
                "id": result.get("id"),
                "self": result.get("self"),
                "summary": summary,
                "project_key": project_key,
                "issue_type": issue_type,
                "assignee": entities.get("assignee")
            }
        
        # Check for specific error types to provide better feedback
        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"]
            # Check for assignee-related errors 
            if "assignee" in error_msg.lower():
                # Provide more specific error message for assignee problems
                return {
                    "success": False,
                    "error": f"Failed to create Jira issue: {error_msg}",
                    "details": "The assignee value was not accepted by Jira. For Jira Cloud, you must use a valid account ID, email address, or username that can be resolved to an account ID."
                }
            
        # Return the original result for other cases
        return result
    except Exception as e:
        logger.error(f"Error in create_jira_issue: {str(e)}", exc_info=True)
        return {"error": str(e)}