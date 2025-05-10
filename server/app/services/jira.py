import os
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
import requests
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.database import get_db, JiraCache, update_jira_cache, get_or_create_user_config, UserConfig

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
        
        if not self.base_url:
            logger.warning("Jira URL not set. Jira functionality will be limited.")
        
        if use_oauth and not user_id:
            logger.warning("User ID not provided for OAuth authentication. Falling back to basic auth.")
            self.use_oauth = False
            
        if not use_oauth and (not self.username or not self.api_token):
            logger.warning("Jira basic auth credentials not set. Jira functionality will be limited.")
        
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
        
        logger.info(f"Initialized Jira client for {self.base_url}")
    
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
        Make a request to the Jira API with retry logic and caching.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: URL parameters
            data: Request data
            use_cache: Whether to use caching
            cache_ttl: Cache TTL in minutes (None for default)
            
        Returns:
            Response from the API as dictionary
        """
        # Use default cache TTL if not specified
        if cache_ttl is None:
            cache_ttl = self.default_cache_ttl
        
        # Generate cache key
        cache_key = self._generate_cache_key(method, endpoint, params, data)
        
        # Return cached response if available
        if use_cache and method.upper() == "GET":
            cached = self._check_jira_cache(cache_key, max_age_minutes=cache_ttl)
            if cached:
                return cached
        
        # Build the full URL
        url = f"{self.base_url}{endpoint}"
        
        # Prepare for retries
        retries = 0
        current_delay = self.retry_delay
        
        while True:
            try:
                logger.debug(f"Making Jira API request: {method} {endpoint}")
                
                # Set up authentication
                headers = self.headers.copy()
                auth = None
                
                if self.use_oauth and self.access_token:
                    # Use OAuth token in Authorization header
                    headers["Authorization"] = f"Bearer {self.access_token}"
                else:
                    # Use basic auth
                    auth = self.get_auth()
                
                # Make the request
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                    auth=auth,
                    timeout=30
                )
                
                # Raise an exception for HTTP errors
                response.raise_for_status()
                
                # Parse the JSON response
                result = response.json()
                
                # Cache GET responses if caching is enabled
                if use_cache and method.upper() == "GET":
                    self._save_to_jira_cache(cache_key, result)
                
                return result
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Jira API request error: {str(e)}")
                
                # Check if we should retry
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exceeded for Jira API request")
                    raise
                
                # Exponential backoff
                logger.info(f"Retrying in {current_delay} seconds (attempt {retries}/{self.max_retries})")
                import time
                time.sleep(current_delay)
                
                # Increase delay for next attempt
                current_delay *= 2
    
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
    
    def create_issue(self, project_key: str = None, issue_type: str = "Task", summary: str = None, 
                    description: Optional[str] = None, 
                    additional_fields: Optional[Dict] = None) -> Dict:
        """
        Create a new issue in Jira.
        
        Args:
            project_key: Project key (e.g., 'PROJECT'). If not provided, uses DEFAULT_JIRA_PROJECT_KEY from settings.
            issue_type: Issue type (e.g., 'Task', 'Bug'). Default is 'Task'.
            summary: Issue summary/title
            description: Issue description
            additional_fields: Additional fields to set on the issue
            
        Returns:
            Created issue details
        """
        endpoint = "/rest/api/2/issue"
        
        # Use default project key if not provided
        if not project_key:
            project_key = settings.DEFAULT_JIRA_PROJECT_KEY
            logger.info(f"Using default project key: {project_key}")
        
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
                    if jira_field == "assignee":
                        # Map to correct assignee structure
                        jira_fields[jira_field] = {"name": entities[key]}
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
            User information
        """
        endpoint = "/rest/api/2/myself"
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