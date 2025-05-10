import os
import json
import logging
import time
import hashlib
import random
from typing import Dict, List, Any, Optional, Union
import requests
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.database import cache_llm_response, check_llm_cache, get_db, LLMCache

# Configure logging
logger = logging.getLogger(__name__)

class OpenRouterClient:
    """
    Client for interacting with the OpenRouter API.
    Handles authentication, sending requests, and error handling.
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    CHAT_ENDPOINT = "/chat/completions"
    
    def __init__(self):
        """Initialize the OpenRouter client with API key from settings."""
        self.api_key = settings.OPENROUTER_API_KEY
        if not self.api_key:
            logger.warning("OpenRouter API key not set. LLM functionality will be limited.")
        
        # Default headers for all requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.SITE_URL,
            "X-Title": settings.API_TITLE
        }
        
        # Set default model from settings
        self.default_model = settings.DEFAULT_LLM_MODEL
        
        # Initialize retry settings
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds
        
        logger.info(f"Initialized OpenRouter client with model {self.default_model}")
    
    def _generate_cache_key(self, model: str, messages: List[Dict[str, str]]) -> str:
        """
        Generate a cache key for the request based on model and messages.
        """
        # Create a string representation of the model and messages
        cache_str = f"{model}:{json.dumps(messages, sort_keys=True)}"
        
        # Create a hash of the string
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _check_cache(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Check if a response is cached for the given model and messages.
        Returns the cached response or None if not found.
        """
        try:
            cache_key = self._generate_cache_key(model, messages)
            
            # Get database session
            db = next(get_db())
            
            # Look for cached response
            cached = check_llm_cache(db, cache_key)
            if cached:
                logger.info(f"Cache hit for prompt: {cache_key[:10]}...")
                return cached.response
            
            logger.debug(f"Cache miss for prompt: {cache_key[:10]}...")
            return None
        except Exception as e:
            logger.error(f"Error checking cache: {str(e)}")
            return None
    
    def _save_to_cache(self, model: str, messages: List[Dict[str, str]], response: str, 
                      tokens_used: int = 0, ttl_hours: int = 24) -> None:
        """
        Save a response to the cache.
        """
        try:
            # Calculate cache key and expiration
            cache_key = self._generate_cache_key(model, messages)
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            
            # Get database session
            db = next(get_db())
            
            # Construct prompt string for storage
            prompt_str = json.dumps(messages, sort_keys=True)
            
            # Cache the response
            cache_llm_response(
                db=db,
                prompt=prompt_str, 
                prompt_hash=cache_key,
                response=response, 
                model=model,
                tokens_used=tokens_used,
                expires_at=expires_at
            )
            
            logger.info(f"Cached response for prompt: {cache_key[:10]}... (expires: {expires_at})")
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: Optional[int] = None,
                             use_cache: bool = True,
                             cache_ttl_hours: int = 24,
                             stream: bool = False) -> Dict[str, Any]:
        """
        Send a chat completion request to the OpenRouter API.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use caching
            cache_ttl_hours: How long to cache the response
            stream: Whether to stream the response
            
        Returns:
            Response from the API or cached response
        """
        # Use default model if none provided
        if not model:
            model = self.default_model
        
        # Check cache first if enabled
        if use_cache and not stream:
            cached_response = self._check_cache(model, messages)
            if cached_response:
                return json.loads(cached_response)
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        # Add max_tokens if provided
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Prepare for retries
        retries = 0
        current_delay = self.retry_delay
        
        while True:
            try:
                logger.debug(f"Sending request to OpenRouter: {model}")
                
                # Make the API request
                response = requests.post(
                    f"{self.BASE_URL}{self.CHAT_ENDPOINT}",
                    headers=self.headers,
                    json=payload,
                    stream=stream,
                    timeout=60  # 60-second timeout
                )
                
                # Raise an exception for HTTP errors
                response.raise_for_status()
                
                if stream:
                    return response  # Return the streaming response object
                
                # Parse the JSON response
                result = response.json()
                
                # Cache the successful response if caching is enabled
                if use_cache:
                    # Extract the text response
                    text_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    # Get tokens used if available
                    tokens_used = result.get("usage", {}).get("total_tokens", 0)
                    # Save to cache
                    self._save_to_cache(
                        model=model,
                        messages=messages,
                        response=json.dumps(result),
                        tokens_used=tokens_used,
                        ttl_hours=cache_ttl_hours
                    )
                
                return result
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                
                # Check if we should retry
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exceeded")
                    raise
                
                # Calculate backoff delay (exponential with jitter)
                delay = current_delay * (1.0 + 0.2 * random.random())
                logger.info(f"Retrying in {delay:.2f} seconds (attempt {retries}/{self.max_retries})")
                time.sleep(delay)
                
                # Increase delay for next attempt
                current_delay *= 2
    
    def get_max_token_limit(self, model: Optional[str] = None) -> int:
        """
        Get the maximum token limit for the specified model or the default model.
        
        Note: While many OpenRouter models support larger context windows (8K-128K tokens),
        some applications and tools artificially limit max_tokens to 1024 tokens.
        This is not an OpenRouter limitation but a client-side restriction
        that we're working around by setting higher limits here.
        
        Args:
            model: The model to get the token limit for (defaults to self.default_model)
            
        Returns:
            The maximum token limit for the model
        """
        # Use default model if none provided
        if not model:
            model = self.default_model
            
        # Map models to their known context limits
        # Most newer models support at least 8K context windows
        model_limits = {
            # Meta/Llama models
            "meta-llama/llama-3-70b-instruct": 8192,
            "meta-llama/llama-3-8b-instruct": 8192,
            # Mistral models
            "mistralai/mistral-7b-instruct": 8192,
            "mistralai/mistral-large-latest": 32768,
            # Claude models accessed via OpenRouter
            "anthropic/claude-3-opus": 128000,
            "anthropic/claude-3-sonnet": 128000,
            "anthropic/claude-3-haiku": 48000,
            # OpenAI models accessed via OpenRouter
            "openai/gpt-4-turbo": 128000,
            "openai/gpt-4": 8192,
            "openai/gpt-3.5-turbo": 16384,
            # Default for any model not explicitly listed
            "default": 4096
        }
        
        # Remove any variant suffixes like :free, :online, etc.
        base_model = model.split(":")[0] if ":" in model else model
        
        # Return the limit for the model or the default if not found
        return model_limits.get(base_model, model_limits["default"])

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Simple wrapper to generate text from a prompt.
        Returns just the text response rather than the full API response.
        
        Args:
            prompt: The text prompt to send
            **kwargs: Additional arguments to pass to chat_completion
            
        Returns:
            Generated text string
        """
        # Construct a simple user message
        messages = [{"role": "user", "content": prompt}]
        
        # Set max_tokens to model limit if not provided
        if "max_tokens" not in kwargs:
            model = kwargs.get("model", self.default_model)
            kwargs["max_tokens"] = min(settings.LLM_MAX_TOKENS, self.get_max_token_limit(model))
        
        # Send the request
        response = await self.chat_completion(messages=messages, **kwargs)
        
        # Extract the text from the response
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting text from response: {str(e)}")
            return ""
    
    async def fallback_response(self, prompt: str) -> str:
        """
        Generate a fallback response when the API is not available.
        Provides context-aware responses for common scenarios.
        
        Args:
            prompt: The user's prompt
            
        Returns:
            A suitable fallback response
        """
        # Check for common task-related queries
        prompt_lower = prompt.lower()
        
        # Jira-specific fallback responses
        if any(word in prompt_lower for word in ["jira", "task", "issue", "ticket", "story"]):
            if any(action in prompt_lower for action in ["create", "add", "new", "make"]):
                return (
                    "I'm currently having trouble connecting to the Jira API to create a new task. "
                    "You can try these alternatives:\n"
                    "1. Try again in a few minutes\n"
                    "2. Create the task directly in Jira\n"
                    "3. Provide more details about the task you want to create so I can help when the connection is restored"
                )
            
            if any(action in prompt_lower for action in ["update", "change", "edit", "modify"]):
                return (
                    "I'm currently having trouble connecting to the Jira API to update tasks. "
                    "Please try again later or make the changes directly in your Jira instance."
                )
            
            if any(action in prompt_lower for action in ["list", "show", "get", "find", "what", "search"]):
                return (
                    "I'm unable to retrieve Jira tasks at the moment due to connection issues. "
                    "Please try again later or check your Jira dashboard directly."
                )
                
            # Generic Jira fallback
            return (
                "I'm sorry, but I'm currently having trouble connecting to the Jira API. "
                "Please try again later or access Jira directly at your organization's Jira URL."
            )
        
        # Reminder-specific fallbacks
        if any(word in prompt_lower for word in ["reminder", "remind", "alert", "notify"]):
            if any(action in prompt_lower for action in ["create", "add", "new", "set"]):
                return (
                    "I'm currently having trouble setting up reminders. "
                    "As an alternative, you could set a reminder in your calendar app or try again later."
                )
                
            if any(action in prompt_lower for action in ["list", "show", "get"]):
                return (
                    "I'm unable to retrieve your reminders at the moment. "
                    "Please try again later or check any existing reminders in your notification center."
                )
                
            # Generic reminder fallback
            return (
                "I'm sorry, but I'm currently having trouble with the reminder system. "
                "Please try again later or use your calendar app for time-sensitive reminders."
            )
            
        # Help-related fallbacks    
        if any(help_word in prompt_lower for help_word in ["help", "how", "can you", "what can", "guide"]):
            return (
                "I can help you manage Jira action items through natural language commands. "
                "I can create tasks, update them, add comments, set reminders, and track evidence. "
                "Some examples of what you can ask:\n\n"
                "• \"Create a new bug in the PROJ project about login issues\"\n"
                "• \"Show my open tasks\"\n"
                "• \"What's the status of PROJ-123?\"\n"
                "• \"Remind me about PROJ-456 tomorrow at 2pm\"\n\n"
                "However, I'm experiencing connection issues at the moment. Please try again later."
            )
            
        # Authentication/permission fallbacks
        if any(word in prompt_lower for word in ["login", "auth", "permission", "access", "token"]):
            return (
                "I'm experiencing authentication issues with the Jira API. "
                "This could be due to expired credentials or permission changes. "
                "Please verify your Jira credentials in the extension settings or contact your administrator."
            )
        
        # Check for specific error patterns that might need specialized responses
        if "rate limit" in prompt_lower or "too many requests" in prompt_lower:
            return (
                "The Jira API is currently rate-limited due to high traffic. "
                "Please wait a few minutes before trying again."
            )
            
        # Generic fallback with instructions for better results
        return (
            "I'm sorry, but I'm having trouble processing your request right now. "
            "This could be due to connectivity issues or temporary service disruption. "
            "Please try again later with a clear, specific request about Jira tasks or reminders."
        )

    # Add method for standardizing response formats
    async def format_response(self, response_data: Dict, intent: str = None) -> str:
        """
        Format the LLM response based on intent and data structure.
        
        Args:
            response_data: The raw response data
            intent: The user's detected intent (optional)
            
        Returns:
            Formatted response string
        """
        try:
            # Extract the text response
            if "choices" in response_data and response_data["choices"]:
                raw_response = response_data["choices"][0]["message"]["content"]
            else:
                return "I couldn't generate a proper response. Please try again."
            
            # Process based on intent if provided
            if intent:
                if intent == "get_tasks" or intent == "get_my_tasks":
                    # Clean up formatting for task lists
                    # Remove markdown list markers that might be inconsistent
                    lines = raw_response.split('\n')
                    formatted_lines = []
                    
                    for line in lines:
                        # Remove markdown list markers and standardize
                        clean_line = line.strip()
                        if clean_line.startswith('- ') or clean_line.startswith('* '):
                            clean_line = '• ' + clean_line[2:]
                        elif clean_line.startswith('1. ') or clean_line.startswith('1) '):
                            clean_line = '• ' + clean_line[3:]
                        formatted_lines.append(clean_line)
                    
                    return '\n'.join(formatted_lines)
                
                elif intent == "get_task_details":
                    # Remove any code blocks or excessive formatting
                    return raw_response.replace('```', '').replace('`', '')
                    
                # Add more intent-specific formatting as needed
            
            # Default: clean up common formatting issues
            cleaned_response = raw_response.replace('```', '').strip()
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return response_data.get("choices", [{}])[0].get("message", {}).get("content", 
                "I couldn't format the response properly. Please try again.")

class JiraPrompts:
    """
    Specialized prompt templates for Jira-specific operations.
    These templates enhance the model's ability to handle Jira-related tasks.
    """
    
    # Task creation templates
    CREATE_TASK = """
    Create a well-formed Jira task with the following information:
    
    Project: {project_key}
    Summary: {summary}
    Description: {description}
    Type: {issue_type}
    Priority: {priority}
    Assignee: {assignee}
    
    Format the task according to Jira specifications, with a clear, concise summary
    and a well-structured description that includes:
    - Background/context
    - Required actions
    - Acceptance criteria (if applicable)
    - Any relevant links or references
    """
    
    # Task update templates
    UPDATE_TASK = """
    Update Jira task {issue_key} with the following changes:
    
    {changes}
    
    Ensure the updates maintain consistency with the existing task and follow
    Jira best practices. When updating fields like status, ensure they are valid
    transitions for the project's workflow.
    """
    
    # Query templates
    TASK_QUERY = """
    Based on the following JQL query results from Jira:
    
    {jql_results}
    
    Provide a clear, concise summary of the tasks focusing on:
    - Total number of tasks
    - Breakdown by status
    - Any tasks requiring immediate attention (high priority or overdue)
    - Recent updates or activity
    
    Format the information in an easy-to-scan way that highlights the most important
    tasks first.
    """
    
    # Task detail template
    TASK_DETAIL = """
    Based on the following Jira task details:
    
    {task_details}
    
    Provide a comprehensive but concise summary that covers:
    - Key information (ID, status, assignee, reporter)
    - Description summary
    - Current progress and blockers (if any)
    - Recent activity or comments
    - Next steps or required actions
    
    Focus on the most actionable information first.
    """
    
    # Comment addition template
    ADD_COMMENT = """
    Compose a well-structured comment for Jira task {issue_key} based on this input:
    
    {comment_text}
    
    Format the comment to be clear and professional, including:
    - Proper formatting (bullet points, etc. when appropriate)
    - Clear, actionable information
    - Relevant links or references
    - Proper mention syntax for any team members (@username)
    """
    
    # Evidence submission template
    ATTACH_EVIDENCE = """
    You're processing evidence to be attached to Jira task {issue_key}.
    
    File to attach: {file_name}
    Context: {context}
    
    Generate a clear comment that:
    - Explains what the evidence shows or proves
    - Relates it to the task requirements
    - Provides any necessary context about the evidence
    - Suggests next steps based on this evidence
    """

    # Add a more specialized template for task formatting
    TASK_FORMATTING = """
    Format the following Jira task data into a clear, human-friendly summary:
    
    ```json
    {task_data}
    ```
    
    Present the information in a structured way that highlights:
    1. The task title, ID and status
    2. Key details like assignee, priority, and due date
    3. A concise summary of the description
    4. Essential information from any comments or attachments
    
    Use bullet points for clarity and keep the formatting consistent.
    """
    
    # Add template for error handling
    ERROR_HANDLING = """
    The user requested information about Jira tasks, but we encountered this error:
    
    {error_message}
    
    Provide a helpful, empathetic response that:
    1. Acknowledges the error without technical details
    2. Suggests alternative actions the user can take
    3. Offers troubleshooting advice if appropriate
    """

class LLMService:
    """
    Service for interacting with LLMs through various providers.
    Currently supports OpenRouter, with fallback options.
    """
    
    def __init__(self):
        """Initialize the LLM service with available providers."""
        self.openrouter = OpenRouterClient()
        logger.info("Initialized LLM service")
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: Optional[int] = None,
                             use_cache: bool = True,
                             stream: bool = False) -> Dict[str, Any]:
        """
        Get a chat completion from the primary LLM provider with fallback options.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            model: Model to use (defaults to the provider's default)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use caching
            stream: Whether to stream the response
            
        Returns:
            Response from the API
        """
        try:
            # Try the primary provider (OpenRouter)
            return await self.openrouter.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                use_cache=use_cache,
                stream=stream
            )
        except Exception as e:
            logger.error(f"Primary LLM provider failed: {str(e)}")
            
            # If we're not streaming, try a fallback provider or method
            if not stream:
                try:
                    if settings.FALLBACK_LLM_MODEL:
                        logger.info(f"Trying fallback model: {settings.FALLBACK_LLM_MODEL}")
                        # Try the same provider with a different model
                        return await self.openrouter.chat_completion(
                            messages=messages,
                            model=settings.FALLBACK_LLM_MODEL,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            use_cache=use_cache,
                            stream=False
                        )
                except Exception as fallback_error:
                    logger.error(f"Fallback LLM model also failed: {str(fallback_error)}")
            
            # If all else fails, return a formatted error response
            error_response = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": await self.openrouter.fallback_response(
                                messages[-1]["content"] if messages else "Unknown request"
                            )
                        },
                        "finish_reason": "error"
                    }
                ],
                "model": model or self.openrouter.default_model,
                "error": str(e)
            }
            return error_response
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text from a simple prompt.
        
        Args:
            prompt: Text prompt
            **kwargs: Additional arguments to pass to chat_completion
            
        Returns:
            Generated text string
        """
        return await self.openrouter.generate_text(prompt, **kwargs)
    
    async def fallback_response(self, prompt: str) -> str:
        """
        Generate a fallback response when all LLM options fail.
        
        Args:
            prompt: The user's prompt
            
        Returns:
            A suitable fallback response
        """
        return await self.openrouter.fallback_response(prompt)
    
    # Add specialized methods for Jira-specific prompts
    async def format_jira_task_creation(self, 
                                       project_key: str, 
                                       summary: str, 
                                       description: str = "",
                                       issue_type: str = "Task",
                                       priority: str = "Medium",
                                       assignee: str = "") -> Dict[str, Any]:
        """
        Format a Jira task creation request with best practices.
        
        Args:
            project_key: Jira project key
            summary: Task summary/title
            description: Task description
            issue_type: Type of issue (Task, Bug, etc.)
            priority: Priority level
            assignee: Username to assign to
            
        Returns:
            Formatted task data ready for Jira API
        """
        # Prepare the prompt with task details
        prompt = JiraPrompts.CREATE_TASK.format(
            project_key=project_key,
            summary=summary,
            description=description or "No description provided.",
            issue_type=issue_type,
            priority=priority,
            assignee=assignee or "Unassigned"
        )
        
        # Get LLM to format and enhance the task
        messages = [
            {"role": "system", "content": "You are an expert Jira task formatter that converts rough task details into well-structured Jira issues."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages=messages, temperature=0.3)
        formatted_text = response["choices"][0]["message"]["content"]
        
        # Extract key pieces from the formatted response
        # This is a simplified approach - in practice, you might want more sophisticated parsing
        lines = formatted_text.split("\n")
        formatted_description = "\n".join([line for line in lines if not any(
            field in line.lower() for field in ["project:", "summary:", "type:", "priority:", "assignee:"]
        )])
        
        # Prepare the final task data
        task_data = {
            "project_key": project_key,
            "summary": summary,
            "description": formatted_description.strip() or description,
            "issue_type": issue_type,
            "priority": priority
        }
        
        # Add assignee if provided
        if assignee:
            task_data["assignee"] = assignee
            
        return task_data
    
    async def format_jira_comment(self, issue_key: str, comment_text: str) -> str:
        """
        Format a comment for a Jira issue with proper structure and formatting.
        
        Args:
            issue_key: The Jira issue key
            comment_text: Raw comment text
            
        Returns:
            Formatted comment text
        """
        # Prepare the prompt
        prompt = JiraPrompts.ADD_COMMENT.format(
            issue_key=issue_key,
            comment_text=comment_text
        )
        
        # Get LLM to format the comment
        messages = [
            {"role": "system", "content": "You are an expert at formatting professional comments for Jira issues."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages=messages, temperature=0.3)
        return response["choices"][0]["message"]["content"]
    
    async def summarize_jira_tasks(self, jql_results: Dict) -> str:
        """
        Summarize a set of Jira tasks from JQL query results.
        
        Args:
            jql_results: Results from a JQL query
            
        Returns:
            Human-readable summary of the tasks
        """
        # Prepare the prompt
        prompt = JiraPrompts.TASK_QUERY.format(
            jql_results=json.dumps(jql_results)
        )
        
        # Get LLM to summarize the tasks
        messages = [
            {"role": "system", "content": "You are an expert at summarizing Jira task information clearly and concisely."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages=messages)
        return response["choices"][0]["message"]["content"]

    async def format_jira_response(self, jira_data: Dict, intent: str) -> str:
        """
        Format Jira API response data into a human-readable format.
        
        Args:
            jira_data: The raw Jira API response
            intent: The user's intent
            
        Returns:
            Formatted string for human consumption
        """
        try:
            # Create a prompt based on the intent and data
            if intent == "get_task_details":
                prompt = JiraPrompts.TASK_DETAIL.format(
                    task_details=json.dumps(jira_data)
                )
            elif intent in ["get_tasks", "get_my_tasks"]:
                prompt = JiraPrompts.TASK_QUERY.format(
                    jql_results=json.dumps(jira_data)
                )
            else:
                # For other intents, use a generic formatting
                prompt = f"Format this Jira data for a {intent} request: {json.dumps(jira_data)}"
            
            # Get LLM to format the data
            messages = [
                {"role": "system", "content": "You are an expert at formatting Jira data into clear, concise summaries."},
                {"role": "user", "content": prompt}
            ]
            
            # Use lower temperature for more consistent formatting
            response = await self.chat_completion(messages=messages, temperature=0.3)
            return response["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Error formatting Jira response: {str(e)}")
            # Provide a basic formatting as fallback
            if intent == "get_task_details" and "fields" in jira_data:
                fields = jira_data["fields"]
                return (
                    f"Task: {jira_data.get('key', 'Unknown')}\n"
                    f"Summary: {fields.get('summary', 'No summary')}\n"
                    f"Status: {fields.get('status', {}).get('name', 'Unknown')}\n"
                    f"Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}\n"
                    f"Description: {fields.get('description', 'No description')[:100]}..."
                )
            elif intent in ["get_tasks", "get_my_tasks"] and "issues" in jira_data:
                # Format a basic list of issues
                response = "Task List:\n"
                for issue in jira_data["issues"][:5]:  # Limit to first 5
                    fields = issue.get("fields", {})
                    response += (
                        f"• {issue.get('key', 'Unknown')}: {fields.get('summary', 'No summary')} "
                        f"({fields.get('status', {}).get('name', 'Unknown')})\n"
                    )
                return response
            
            # Generic fallback
            return f"Jira data retrieved successfully. Use specific commands to see details."

# Initialize and export the LLM service
llm_service = LLMService() 