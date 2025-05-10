import logging
from typing import Dict, List, Any, Optional
import json
import re
import nltk
from datetime import datetime, timedelta
import dateparser
import hashlib
import os

from app.core.config import settings
from app.services.llm import OpenRouterClient

logger = logging.getLogger(__name__)

# Initialize NLTK for more advanced text processing
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
    logger.info("NLTK data found successfully")
except LookupError as e:
    logger.warning(f"NLTK data not found: {str(e)}")
    logger.info("Downloading required NLTK data...")
    try:
        # Create directory if it doesn't exist
        nltk_dir = os.path.join(os.path.expanduser("~"), "nltk_data")
        os.makedirs(nltk_dir, exist_ok=True)
        
        # Download required data
        nltk.download('punkt', download_dir=nltk_dir)
        nltk.download('averaged_perceptron_tagger', download_dir=nltk_dir)
        logger.info("NLTK data downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download NLTK data: {str(e)}")
        logger.warning("Will use fallback tokenization methods")


class PromptTemplate:
    """
    A template for generating prompts with placeholders.
    """
    
    def __init__(self, template: str,
                 required_entities: Optional[List[str]] = None):
        """
        Initialize a prompt template.
        
        Args:
            template: String template with {placeholders}
            required_entities: List of entity names that must be provided
        """
        self.template = template
        self.required_entities = required_entities or []
    
    def format(self, **kwargs) -> str:
        """
        Format the template with the provided values.
        
        Args:
            **kwargs: Key-value pairs to substitute in the template
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValueError: If required entities are missing
        """
        # Check for required entities
        missing = [
            entity for entity in self.required_entities if entity not in kwargs]
        if missing:
            raise ValueError(
                f"Missing required entities for prompt template: {
                    ', '.join(missing)}")
        
        # Format the template
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            # Handle missing keys more gracefully
            logger.error(f"Error formatting prompt template: {str(e)}")
            raise ValueError(f"Missing key in prompt template: {str(e)}")


class JiraPrompts:
    """
    Collection of prompt templates for Jira-related tasks.
    """

    # Template for extracting entities from text for Jira issue creation
    CREATE_ISSUE_EXTRACT = PromptTemplate("""
    Extract structured information from the following text to create a Jira issue:

    TEXT: "{text}"

    Return the following information in a structured JSON format:
    - summary: A concise title for the issue (required)
    - description: A detailed description of the issue (optional)
    - issue_type: The type of issue (e.g., "Task", "Bug", "Story") (default: "Task")
    - priority: The priority level (e.g., "High", "Medium", "Low") (default: "Medium")
    - assignee: The username of the person to assign the issue to (optional)
    - due_date: The due date in YYYY-MM-DD format (optional)
    - labels: A list of labels/tags (optional)

    Only extract information that is explicitly mentioned in the text. Do not make assumptions or add information not present in the text.

    Format your response as a valid JSON object with only the fields mentioned above.
    """, ["text"])

    # Template for extracting entities from text for Jira issue updates
    UPDATE_ISSUE_EXTRACT = PromptTemplate("""
    Extract structured information from the following text to update a Jira issue:

    TEXT: "{text}"
    ISSUE_KEY: "{issue_key}"

    Return the following information in a structured JSON format, only including fields that should be updated:
    - summary: A concise title for the issue (if it should be changed)
    - description: A detailed description of the issue (if it should be changed)
    - priority: The priority level (e.g., "High", "Medium", "Low") (if it should be changed)
    - assignee: The username of the person to assign the issue to (if it should be changed)
    - due_date: The due date in YYYY-MM-DD format (if it should be changed)
    - labels: A list of labels/tags (if they should be changed)
    - status_transition: The status to transition the issue to (e.g., "In Progress", "Done") (if it should be changed)

    Only extract information that is explicitly mentioned in the text. Do not make assumptions or add information not present in the text.

    Format your response as a valid JSON object with only the fields that need to be updated.
    """, ["text", "issue_key"])

    # Template for extracting entities from text for Jira issue searching
    SEARCH_ISSUES_EXTRACT = PromptTemplate("""
    Extract structured information from the following text to search for Jira issues:

    TEXT: "{text}"

    Return the following information in a structured JSON format:
    - project: The project key to search in (optional)
    - issue_type: The type of issue to search for (e.g., "Task", "Bug", "Story") (optional)
    - status: The status to filter by (e.g., "Open", "In Progress", "Done") (optional)
    - assignee: The username of the assignee to filter by (optional)
    - reporter: The username of the reporter to filter by (optional)
    - labels: A list of labels/tags to filter by (optional)
    - created_after: The date in YYYY-MM-DD format to filter issues created after (optional)
    - created_before: The date in YYYY-MM-DD format to filter issues created before (optional)
    - updated_after: The date in YYYY-MM-DD format to filter issues updated after (optional)
    - updated_before: The date in YYYY-MM-DD format to filter issues updated before (optional)
    - due_after: The date in YYYY-MM-DD format to filter issues due after (optional)
    - due_before: The date in YYYY-MM-DD format to filter issues due before (optional)
    - keywords: Keywords to search for in the issue summary or description (optional)
    - max_results: Maximum number of results to return (optional, default: 50)
    - order_by: Field to order results by (optional, default: "updated")
    - order_direction: Direction to order results ("ASC" or "DESC") (optional, default: "DESC")

    Only extract information that is explicitly mentioned in the text. Do not make assumptions or add information not present in the text.

    Format your response as a valid JSON object with only the fields mentioned above that are relevant to the search query.
    """, ["text"])

    # Template for extracting entities from text for adding a comment to a
    # Jira issue
    ADD_COMMENT_EXTRACT = PromptTemplate("""
    Extract structured information from the following text to add a comment to a Jira issue:

    TEXT: "{text}"
    ISSUE_KEY: "{issue_key}"

    Return the following information in a structured JSON format:
    - comment: The text of the comment to add (required)
    - visibility: The visibility of the comment, if specified (optional, can be "Developers", "Administrators", etc.)

    Only extract information that is explicitly mentioned in the text. Do not make assumptions or add information not present in the text.

    Format your response as a valid JSON object with only the fields mentioned above.
    """, ["text", "issue_key"])

    # Template for analyzing text to identify the Jira intent
    IDENTIFY_INTENT = PromptTemplate("""
    Determine the Jira action intent from the following text:

    TEXT: "{text}"

    Choose one of the following intents:
    - CREATE_ISSUE: Creating a new Jira issue
    - UPDATE_ISSUE: Updating an existing Jira issue
    - SEARCH_ISSUES: Searching for Jira issues
    - GET_ISSUE: Retrieving details of a specific Jira issue
    - ADD_COMMENT: Adding a comment to a Jira issue
    - TRANSITION_ISSUE: Changing the status of a Jira issue
    - ASSIGN_ISSUE: Assigning a Jira issue to someone
    - UNKNOWN: The text does not indicate a Jira action

    Also extract the issue key if present in the text (in the format PROJECT-123).

    Format your response as a valid JSON object with the following fields:
    - intent: The identified intent
    - issue_key: The issue key if present, null otherwise
    - confidence: A value between 0 and 1 indicating your confidence in the intent classification

    Example response:
    {{"intent": "UPDATE_ISSUE", "issue_key": "PROJ-123", "confidence": 0.95}}
    """, ["text"])


class PromptManager:
    """
    Manager for selecting and populating prompt templates.
    """
    
    # System prompt to set the assistant's role
    SYSTEM_PROMPT = """You are a helpful assistant that manages Jira tasks and action items. 
Your role is to help the user track their tasks, set reminders, and provide updates.
Be concise, professional, and action-oriented in your responses.
Always focus on being helpful and practical.
You should respond to natural language requests about creating, updating, and tracking Jira issues."""

    # Expanded patterns for entity extraction
    patterns = {
        # e.g., JIRA-123, TASK-456, ABC123-789
        "task_id": r'\b([A-Z][A-Z0-9_]+-\d+)\b',
        # e.g., project PROJ, in DEMO
        "project_key": r'\b(project|in|for)\s+([A-Z][A-Z0-9_]+)\b',
        "datetime": r'\b(\d{1,2}[:/]\d{1,2}(?:[:/]\d{2,4})?)\b|\b(\d{1,2}(?:am|pm))\b|\b(tomorrow|today|next week|next month|in \d+ days?)\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "username": r'\b@([A-Za-z0-9._-]+)\b',  # e.g., @john.doe
        "duration": r'\b(\d+)\s+(minute|minutes|mins|min|hour|hours|day|days|week|weeks|month|months)s?\b',
        "priority": r'\b(highest|high|medium|low|lowest|blocker|critical|major|minor|trivial)\s+priority\b',
        "status": r'\b(to do|in progress|done|blocked|pending|completed|resolved|open|closed)\b',
        "issue_type": r'\b(bug|task|story|epic|feature|improvement|sub-task)\b',
        # Common file extensions
        "file_name": r'\b([a-zA-Z0-9_.-]+\.(pdf|doc|docx|jpg|jpeg|png|xlsx|txt|zip))\b',
    }
    
    # Additional keyword dictionaries for better intent matching
    keywords = {
        "task_actions": ["create", "add", "make", "new", "update", "edit", "change", "modify", "delete", "remove", "assign", "transition", "move"],
        "task_objects": ["task", "issue", "ticket", "story", "bug", "feature", "item", "action item", "epic", "subtask"],
        "reminder_actions": ["remind", "remember", "notification", "alert", "ping", "notify", "follow up"],
        "time_references": ["tomorrow", "today", "next week", "later", "soon", "in an hour", "after lunch", "by EOD", "by end of day", "by COB"],
        "list_actions": ["show", "list", "get", "view", "display", "what are", "find", "search", "query", "fetch"],
        "evidence_actions": ["attach", "upload", "evidence", "file", "document", "screenshot", "proof", "add file"],
        "question_words": ["how", "what", "when", "why", "where", "who", "which", "can", "could", "would"],
        "status_terms": {
            "to do": ["to do", "todo", "not started", "open", "new"],
            "in progress": ["in progress", "working on", "started", "ongoing", "in dev", "developing"],
            "done": ["done", "complete", "finished", "resolved", "closed", "fixed"],
            "blocked": ["blocked", "stuck", "impediment", "waiting", "on hold"]
        },
        "priority_terms": {
            "highest": ["highest", "blocker", "critical", "urgent", "asap", "emergency", "p0"],
            "high": ["high", "important", "major", "p1"],
            "medium": ["medium", "normal", "default", "standard", "p2"],
            "low": ["low", "minor", "can wait", "when possible", "p3"],
            "lowest": ["lowest", "trivial", "whenever", "no rush", "p4"]
        }
    }

    # Templates for different intents
    templates = {
        # Task retrieval templates
        "get_tasks": PromptTemplate(
            "List the following Jira tasks {filter_clause}. {additional_instructions}",
            []  # Make filter_clause optional
        ),
        "get_task_details": PromptTemplate(
            "Provide detailed information about Jira task {task_id}. Include status, assignee, description, and any comments. {additional_instructions}",
            ["task_id"]
        ),
        "get_my_tasks": PromptTemplate(
            "List all Jira tasks currently assigned to {assignee}. {status_filter} {additional_instructions}",
            ["assignee"]
        ),
        
        # Task creation and update templates
        "create_task": PromptTemplate(
            "Create a new Jira task with these details:\nProject: {project_key}\nType: {issue_type}\nTitle: {title}\nDescription: {description}\n"
            "Priority: {priority}\nAssignee: {assignee}\n{additional_fields}",
            ["title", "project_key"]  # Only require title and project_key
        ),
        "update_task": PromptTemplate(
            "Update Jira task {task_id} with the following changes:\n{changes}",
            ["task_id", "changes"]
        ),
        "add_comment": PromptTemplate(
            "Add the following comment to Jira task {task_id}:\n{comment}",
            ["task_id", "comment"]
        ),
        "transition_task": PromptTemplate(
            "Change the status of Jira task {task_id} to {status}. {comment}",
            ["task_id", "status"]
        ),
        "assign_task": PromptTemplate(
            "Assign Jira task {task_id} to {assignee}. {comment}",
            ["task_id", "assignee"]
        ),
        
        # Reminder templates
        "create_reminder": PromptTemplate(
            "Create a reminder for task {task_id} at {reminder_time} with message: {message}",
            ["task_id", "reminder_time"]
        ),
        "list_reminders": PromptTemplate(
            "List all my reminders {filter_clause}",
            []  # No required entities
        ),
        "get_overdue_tasks": PromptTemplate(
            "List all overdue Jira tasks {assignee_filter}. {additional_instructions}",
            []  # No required entities
        ),

        # Evidence and attachment templates
        "attach_evidence": PromptTemplate(
            "Attach the file named {file_name} as evidence to Jira task {task_id} with the comment: {comment}",
            ["task_id", "file_name"]
        ),
        
        # General help
        "help": PromptTemplate(
            "Provide help with {topic} in the context of Jira task management.",
            []  # No required entities
        ),
        
        # Fallback for unknown intents
        "unknown": PromptTemplate(
            "I'm not sure what you're asking about Jira tasks. {original_query}\n\n"
            "I can help with creating, updating, querying, and managing Jira tasks and action items. Can you rephrase your request?",
            ["original_query"]
        )
    }
    
    def __init__(self):
        """Initialize the prompt manager with templates and LLM client."""
        self.llm_client = OpenRouterClient()
        self.jira_prompts = JiraPrompts()

        # Define the default project key
        self.default_project_key = settings.DEFAULT_JIRA_PROJECT_KEY
    
    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """
        Normalize text for more consistent processing
        """
        # Convert to lowercase
        text = text.lower()
        
        # Replace common abbreviations
        abbreviations = {
            "asap": "as soon as possible",
            "wrt": "with respect to",
            "w/": "with",
            "w/o": "without",
            "tmrw": "tomorrow",
            "tdy": "today",
            "eod": "end of day",
            "cob": "close of business",
            "pls": "please",
            "fyi": "for your information",
            "jira": "jira",
        }
        
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
            
        return text
    
    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, Any]:
        """
        Extract entities from the user's text with enhanced detection.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary of extracted entities
        """
        # Basic validation of input
        if not text or not isinstance(text, str):
            logger.warning("Invalid input to extract_entities: empty or non-string input")
            return {"original_query": ""}
            
        # Sanitize the input text
        try:
            # Truncate very long inputs
            text = text[:1000]  
            # Basic cleanup of invalid characters
            text = re.sub(r'[^\w\s.,;:!?\'"-=+*/\\@#$%^&(){}\[\]<>|]', ' ', text).strip()
        except Exception as e:
            logger.error(f"Error sanitizing input text: {str(e)}")
            return {"original_query": text}
            
        entities = {
            "original_query": text
        }
        
        # Store original case for pattern matching on task IDs, etc.
        original_text = text

        # Normalize text for intent and keyword detection
        try:
            normalized_text = cls._normalize_text(text)
        except Exception as e:
            logger.error(f"Error normalizing text: {str(e)}")
            normalized_text = text.lower()
        
        # Tokenize for part-of-speech tagging
        try:
            tokens = nltk.word_tokenize(normalized_text)
            pos_tags = nltk.pos_tag(tokens)
        except LookupError:
            # Handle missing NLTK data by using a simple fallback tokenizer
            logger.warning("NLTK punkt tokenizer not available. Using basic fallback tokenization.")
            tokens = normalized_text.split()
            pos_tags = [(token, 'NN') for token in tokens]  # Default to nouns
        except Exception as e:
            logger.error(f"Error during tokenization: {str(e)}")
            # Very basic fallback
            tokens = normalized_text.split()
            pos_tags = [(token, 'NN') for token in tokens]
            
        # Extract entities using patterns, with error handling for each pattern
        try:
            # Extract task IDs with standard pattern
            task_id_matches = re.findall(cls.patterns["task_id"], original_text)
            if task_id_matches:
                entities["task_id"] = task_id_matches[0]
        except Exception as e:
            logger.error(f"Error extracting task IDs: {str(e)}")
            
        try:
            # Extract project key
            project_matches = re.findall(cls.patterns["project_key"], original_text)
            if project_matches:
                # The second group contains the actual project key
                entities["project_key"] = project_matches[0][1]
        except Exception as e:
            logger.error(f"Error extracting project key: {str(e)}")
            
        # Continue with the rest of the entity extraction with similar error handling
        
        return entities
    
    @classmethod
    def detect_intent(cls, text: str) -> str:
        """
        Detect the user's intent from their message.
        
        Args:
            text: User input text
            
        Returns:
            String representing the detected intent
        """
        # Normalize the text
        normalized_text = cls._normalize_text(text)
        entities = cls.extract_entities(text)

        # Specific task ID with various actions
        has_task_id = "task_id" in entities

        # Check for task creation intent
        if any(word in normalized_text for word in ["create", "add", "new"]) and any(
                word in normalized_text for word in cls.keywords["task_objects"]):
            return "create_task"
        
        # Check for task update intent
        if has_task_id and any(word in normalized_text for word in [
                               "update", "change", "modify", "edit"]):
            return "update_task"
        
        # Check for status transition intent
        if has_task_id and any(word in normalized_text for word in [
                               "transition", "move", "change status", "mark as"]) and "status" in entities:
            return "transition_task"

        # Check for assignment intent
        if has_task_id and any(word in normalized_text for word in [
                               "assign", "give to", "transfer to"]) and "assignee" in entities:
            return "assign_task"

        # Check for comment adding intent
        if has_task_id and any(word in normalized_text for word in [
                               "comment", "note", "remark"]) and "comment" in entities:
            return "add_comment"

        # Check for task detail intent
        if has_task_id and any(word in normalized_text for word in [
                               "detail", "about", "info", "information", "describe", "show"]):
            return "get_task_details"

        # Check for attachment/evidence intent
        if has_task_id and any(
                word in normalized_text for word in cls.keywords["evidence_actions"]) and "file_name" in entities:
            return "attach_evidence"

        # Check for reminder creation intent
        if has_task_id and any(
                word in normalized_text for word in cls.keywords["reminder_actions"]) and "reminder_time" in entities:
                return "create_reminder"

        # Check for task listing intents
        if any(word in normalized_text for word in cls.keywords["list_actions"]) and any(
                word in normalized_text for word in cls.keywords["task_objects"]):
            # If the user mentions "my tasks", use the specialized intent
            if "my" in normalized_text or "me" in normalized_text or "I'm" in normalized_text or "assigned to me" in normalized_text:
                return "get_my_tasks"
            # If looking for overdue tasks
            elif "overdue" in normalized_text:
                return "get_overdue_tasks"
            # General task listing
            else:
                return "get_tasks"

        # Check for reminder listing intent
        if any(word in normalized_text for word in cls.keywords["list_actions"]) and any(
                word in normalized_text for word in cls.keywords["reminder_actions"]):
                return "list_reminders"
        
        # Check for help intent
        if any(word in normalized_text for word in [
               "help", "how do I", "how to", "explain", "guide"]):
            return "help"
        
        # Default to unknown if no intent is matched
        return "unknown"
    
    @classmethod
    def build_messages(
            cls, intent: str, entities: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build the list of messages for the LLM based on intent and entities.
        
        Args:
            intent: Detected intent
            entities: Extracted entities
            
        Returns:
            List of messages (system, user) for the LLM
        """
        messages = [{"role": "system", "content": cls.SYSTEM_PROMPT}]

        # Get the appropriate template for the intent
        template = cls.templates.get(intent, cls.templates["unknown"])

        try:
            # Format the template with the entities
            prompt = template.format(**entities)

            # Add the formatted prompt as a user message
            messages.append({"role": "user", "content": prompt})

        except ValueError as e:
            # If required entities are missing, fall back to unknown intent
            logger.warning(f"Missing entities for intent {intent}: {str(e)}")
            unknown_template = cls.templates["unknown"]
            prompt = unknown_template.format(**entities)
            messages.append({"role": "user", "content": prompt})
        except KeyError as e:
            # If a key is missing, log it and fall back to unknown intent
            logger.error(f"Error formatting prompt template: {str(e)}")
            unknown_template = cls.templates["unknown"]
            prompt = unknown_template.format(**entities)
            messages.append({"role": "user", "content": prompt})
        
        return messages
    
    @classmethod
    def process_user_input(cls, text: str) -> Dict[str, Any]:
        """
        Process user input text to identify intent and extract entities.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary with processed data:
            - intent: Identified intent
            - entities: Extracted entities
            - messages: LLM messages for the intent
        """
        # Extract entities from the text
        entities = cls.extract_entities(text)
        
        # Detect the intent from the text
        intent = cls.detect_intent(text)
        
        # Set default values for commonly used fields
        if "description" not in entities:
            entities["description"] = "No description provided"
            
        if "filter_clause" not in entities:
            entities["filter_clause"] = "for the current user"
            
        if "assignee" not in entities:
            entities["assignee"] = "current user"
            
        if "comment" not in entities:
            entities["comment"] = ""
            
        if "additional_instructions" not in entities:
            entities["additional_instructions"] = ""
            
        if "additional_fields" not in entities:
            entities["additional_fields"] = ""
            
        if "status_filter" not in entities:
            entities["status_filter"] = ""
            
        # If project_key is not provided but we need it (create task intent),
        # use the default project key from settings
        if intent == "create_task" and "project_key" not in entities:
            entities["project_key"] = settings.DEFAULT_JIRA_PROJECT_KEY
            logger.info(f"Using default project key: {entities['project_key']}")

        # Build the messages for the LLM
        messages = cls.build_messages(intent, entities)
        
        return {
            "intent": intent,
            "entities": entities,
            "messages": messages
        }


# Create singleton instance
prompt_manager = PromptManager() 
