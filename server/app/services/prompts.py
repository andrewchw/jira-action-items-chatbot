import logging
from typing import Dict, List, Any, Optional
import json
import re
import nltk
from datetime import datetime, timedelta
import dateparser

logger = logging.getLogger(__name__)

# Initialize NLTK for more advanced text processing
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer")
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    logger.info("Downloading NLTK perceptron tagger")
    nltk.download('averaged_perceptron_tagger', quiet=True)

class PromptTemplate:
    """
    A template for generating prompts with placeholders.
    """
    
    def __init__(self, template: str, required_entities: Optional[List[str]] = None):
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
        missing = [entity for entity in self.required_entities if entity not in kwargs]
        if missing:
            raise ValueError(f"Missing required entities for prompt template: {', '.join(missing)}")
        
        # Format the template
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            # Handle missing keys more gracefully
            logger.error(f"Error formatting prompt template: {str(e)}")
            raise ValueError(f"Missing key in prompt template: {str(e)}")

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

    # Templates for different intents
    TEMPLATES = {
        # Task retrieval templates
        "get_tasks": PromptTemplate(
            "List the following Jira tasks {filter_clause}. {additional_instructions}",
            ["filter_clause"]
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
            ["project_key", "title"]
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
    
    # Expanded patterns for entity extraction
    PATTERNS = {
        "task_id": r'\b([A-Z][A-Z0-9_]+-\d+)\b',  # e.g., JIRA-123, TASK-456, ABC123-789
        "project_key": r'\b(project|in|for)\s+([A-Z][A-Z0-9_]+)\b',  # e.g., project PROJ, in DEMO
        "datetime": r'\b(\d{1,2}[:/]\d{1,2}(?:[:/]\d{2,4})?)\b|\b(\d{1,2}(?:am|pm))\b|\b(tomorrow|today|next week|next month|in \d+ days?)\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "username": r'\b@([A-Za-z0-9._-]+)\b',  # e.g., @john.doe
        "duration": r'\b(\d+)\s+(minute|minutes|mins|min|hour|hours|day|days|week|weeks|month|months)s?\b',
        "priority": r'\b(highest|high|medium|low|lowest|blocker|critical|major|minor|trivial)\s+priority\b',
        "status": r'\b(to do|in progress|done|blocked|pending|completed|resolved|open|closed)\b',
        "issue_type": r'\b(bug|task|story|epic|feature|improvement|sub-task)\b',
        "file_name": r'\b([a-zA-Z0-9_.-]+\.(pdf|doc|docx|jpg|jpeg|png|xlsx|txt|zip))\b',  # Common file extensions
    }
    
    # Additional keyword dictionaries for better intent matching
    KEYWORDS = {
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
        entities = {
            "original_query": text
        }
        
        # Store original case for pattern matching on task IDs, etc.
        original_text = text
        
        # Normalize text for intent and keyword detection
        normalized_text = cls._normalize_text(text)
        
        # Tokenize for part-of-speech tagging
        tokens = nltk.word_tokenize(normalized_text)
        pos_tags = nltk.pos_tag(tokens)
        
        # Extract task IDs with standard pattern
        task_id_matches = re.findall(cls.PATTERNS["task_id"], original_text)
        if task_id_matches:
            entities["task_id"] = task_id_matches[0]
        
        # Extract project key
        project_matches = re.findall(cls.PATTERNS["project_key"], original_text)
        if project_matches:
            # The second group contains the actual project key
            entities["project_key"] = project_matches[0][1]
        
        # Extract datetime references and parse them
        datetime_matches = re.findall(cls.PATTERNS["datetime"], normalized_text)
        if datetime_matches:
            # Flatten the matches (findall returns tuples for groups)
            date_values = [val for match in datetime_matches for val in match if val]
            if date_values:
                date_str = date_values[0]
                entities["reminder_time_raw"] = date_str
                
                # Try to parse the date using dateparser for more human-friendly parsing
                parsed_date = dateparser.parse(date_str)
                if parsed_date:
                    entities["reminder_time"] = parsed_date.isoformat()
                else:
                    # Fallback to just storing the raw string
                    entities["reminder_time"] = date_str
        
        # Extract email addresses for assignee
        email_matches = re.findall(cls.PATTERNS["email"], text)
        if email_matches:
            entities["assignee"] = email_matches[0]
        else:
            # Try to extract usernames with @ prefix
            username_matches = re.findall(cls.PATTERNS["username"], text)
            if username_matches:
                entities["assignee"] = username_matches[0]
            elif "me" in tokens or "my" in tokens or "myself" in tokens:
                # Mark as self-assignment
                entities["assignee"] = "current_user"
        
        # Extract issue type
        issue_type_matches = re.findall(cls.PATTERNS["issue_type"], normalized_text)
        if issue_type_matches:
            entities["issue_type"] = issue_type_matches[0]
        else:
            # Default issue type
            entities["issue_type"] = "Task"
        
        # Extract priority
        priority_matches = re.findall(cls.PATTERNS["priority"], normalized_text)
        if priority_matches:
            priority = priority_matches[0]
            # Normalize priority values using the priority terms dictionary
            for norm_priority, synonyms in cls.KEYWORDS["priority_terms"].items():
                if priority.lower() in synonyms:
                    entities["priority"] = norm_priority
                    break
            # If not found in known priorities, use the matched value
            if "priority" not in entities:
                entities["priority"] = priority
        else:
            # Check for priority in the text
            for norm_priority, synonyms in cls.KEYWORDS["priority_terms"].items():
                if any(word in normalized_text for word in synonyms):
                    entities["priority"] = norm_priority
                    break
            
            # Default priority if not found
            if "priority" not in entities:
                entities["priority"] = "medium"
        
        # Extract status
        status_matches = re.findall(cls.PATTERNS["status"], normalized_text)
        if status_matches:
            status = status_matches[0]
            # Normalize status values using the status terms dictionary
            for norm_status, synonyms in cls.KEYWORDS["status_terms"].items():
                if status.lower() in synonyms:
                    entities["status"] = norm_status
                    break
            # If not found in known statuses, use the matched value
            if "status" not in entities:
                entities["status"] = status
        else:
            # Check for status in the text
            for norm_status, synonyms in cls.KEYWORDS["status_terms"].items():
                if any(word in normalized_text for word in synonyms):
                    entities["status"] = norm_status
                    break
        
        # Extract file name for attachments
        file_matches = re.findall(cls.PATTERNS["file_name"], original_text)
        if file_matches:
            entities["file_name"] = file_matches[0][0]  # First group is the filename with extension
        
        # Extract task title and description for create operations
        if "create" in normalized_text or "add" in normalized_text or "new" in normalized_text:
            # Look for potential task title - often follows "titled", "called", or after certain keywords
            title_patterns = [
                r'(?:titled|called|named)\s+"([^"]+)"',
                r'(?:titled|called|named)\s+\'([^\']+)\'',
                r'(?:titled|called|named)\s+([^.,;:]+)',
                r'(?:create|add|new)\s+(?:a|an)\s+(?:task|issue|ticket)\s+(?:for|about|on)\s+([^.,;:]+)',
                r'(?:create|add|new)\s+(?:a|an)\s+(?:task|issue|ticket)\s+(?:titled|called|named)\s+([^.,;:]+)',
            ]
            
            for pattern in title_patterns:
                title_match = re.search(pattern, normalized_text)
                if title_match:
                    entities["title"] = title_match.group(1).strip()
                    break
            
            # If no title found by patterns but we have tokens, extract noun phrases
            if "title" not in entities:
                # Extract noun phrases as potential task titles
                noun_phrases = []
                current_np = []
                
                for token, tag in pos_tags:
                    if tag.startswith('NN'):  # Noun types
                        current_np.append(token)
                    elif current_np:
                        noun_phrases.append(' '.join(current_np))
                        current_np = []
                
                if current_np:  # Don't forget the last one
                    noun_phrases.append(' '.join(current_np))
                
                # Use the longest noun phrase as the title if available
                if noun_phrases:
                    entities["title"] = max(noun_phrases, key=len)
        
        # Extract comment text
        comment_patterns = [
            r'(?:comment|note)(?:ing)?\s+"([^"]+)"',
            r'(?:comment|note)(?:ing)?\s+\'([^\']+)\'',
            r'(?:comment|note)(?:ing)?\s+(?:that|saying|stating)\s+([^.,;:]+)',
            r'(?:with|and|add)\s+(?:the|a)\s+(?:comment|note)\s+"([^"]+)"',
            r'(?:with|and|add)\s+(?:the|a)\s+(?:comment|note)\s+\'([^\']+)\'',
            r'(?:with|and|add)\s+(?:the|a)\s+(?:comment|note)\s+([^.,;:]+)',
        ]
        
        for pattern in comment_patterns:
            comment_match = re.search(pattern, normalized_text)
            if comment_match:
                entities["comment"] = comment_match.group(1).strip()
                break
        
        # Extract changes for update task
        if "update" in normalized_text or "change" in normalized_text or "modify" in normalized_text:
            changes = []
            
            # Extract description changes
            desc_patterns = [
                r'(?:change|update|modify|set)\s+(?:the)?\s*description\s+(?:to|as)\s+"([^"]+)"',
                r'(?:change|update|modify|set)\s+(?:the)?\s*description\s+(?:to|as)\s+\'([^\']+)\'',
                r'(?:change|update|modify|set)\s+(?:the)?\s*description\s+(?:to|as)\s+([^.,;:]+)',
            ]
            
            for pattern in desc_patterns:
                desc_match = re.search(pattern, normalized_text)
                if desc_match:
                    changes.append(f"Description: {desc_match.group(1).strip()}")
                    break
            
            # Extract summary/title changes
            summary_patterns = [
                r'(?:change|update|modify|set)\s+(?:the)?\s*(?:summary|title)\s+(?:to|as)\s+"([^"]+)"',
                r'(?:change|update|modify|set)\s+(?:the)?\s*(?:summary|title)\s+(?:to|as)\s+\'([^\']+)\'',
                r'(?:change|update|modify|set)\s+(?:the)?\s*(?:summary|title)\s+(?:to|as)\s+([^.,;:]+)',
            ]
            
            for pattern in summary_patterns:
                summary_match = re.search(pattern, normalized_text)
                if summary_match:
                    changes.append(f"Summary: {summary_match.group(1).strip()}")
                    break
            
            # Check for priority changes
            if "priority" in entities:
                changes.append(f"Priority: {entities['priority']}")
            
            # If we have changes, join them
            if changes:
                entities["changes"] = "\n".join(changes)
        
        # Extract filter clause for get tasks
        if any(word in normalized_text for word in ["list", "show", "get", "find"]):
            filter_parts = []
            
            # Filter by assignee
            if "assignee" in entities:
                filter_parts.append(f"assigned to {entities['assignee']}")
            elif "myself" in normalized_text or "me" in normalized_text or "my" in normalized_text:
                filter_parts.append("assigned to me")
                entities["assignee"] = "current_user"
            
            # Filter by status
            if "status" in entities:
                filter_parts.append(f"with status '{entities['status']}'")
            
            # Filter by priority
            if "priority" in entities and "list" in normalized_text:
                filter_parts.append(f"with priority '{entities['priority']}'")
            
            # Check for overdue or upcoming tasks
            if "overdue" in normalized_text:
                filter_parts.append("that are overdue")
            elif "upcoming" in normalized_text or "this week" in normalized_text:
                filter_parts.append("due this week")
            
            # Filter by project
            if "project_key" in entities:
                filter_parts.append(f"in project {entities['project_key']}")
            
            # Join all filter parts
            if filter_parts:
                entities["filter_clause"] = " ".join(filter_parts)
            else:
                entities["filter_clause"] = "for the current user"
            
            # Add status filter specifically for get_my_tasks
            if "status" in entities:
                entities["status_filter"] = f"Show only tasks with status '{entities['status']}'."
            else:
                entities["status_filter"] = ""
        
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
        if any(word in normalized_text for word in ["create", "add", "new"]) and any(word in normalized_text for word in cls.KEYWORDS["task_objects"]):
            return "create_task"
        
        # Check for task update intent
        if has_task_id and any(word in normalized_text for word in ["update", "change", "modify", "edit"]):
            return "update_task"
        
        # Check for status transition intent
        if has_task_id and any(word in normalized_text for word in ["transition", "move", "change status", "mark as"]) and "status" in entities:
            return "transition_task"
        
        # Check for assignment intent
        if has_task_id and any(word in normalized_text for word in ["assign", "give to", "transfer to"]) and "assignee" in entities:
            return "assign_task"
        
        # Check for comment adding intent
        if has_task_id and any(word in normalized_text for word in ["comment", "note", "remark"]) and "comment" in entities:
            return "add_comment"
        
        # Check for task detail intent
        if has_task_id and any(word in normalized_text for word in ["detail", "about", "info", "information", "describe", "show"]):
            return "get_task_details"
        
        # Check for attachment/evidence intent
        if has_task_id and any(word in normalized_text for word in cls.KEYWORDS["evidence_actions"]) and "file_name" in entities:
            return "attach_evidence"
        
        # Check for reminder creation intent
        if has_task_id and any(word in normalized_text for word in cls.KEYWORDS["reminder_actions"]) and "reminder_time" in entities:
            return "create_reminder"
        
        # Check for task listing intents
        if any(word in normalized_text for word in cls.KEYWORDS["list_actions"]) and any(word in normalized_text for word in cls.KEYWORDS["task_objects"]):
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
        if any(word in normalized_text for word in cls.KEYWORDS["list_actions"]) and any(word in normalized_text for word in cls.KEYWORDS["reminder_actions"]):
            return "list_reminders"
        
        # Check for help intent
        if any(word in normalized_text for word in ["help", "how do I", "how to", "explain", "guide"]):
            return "help"
        
        # Default to unknown if no intent is matched
        return "unknown"
    
    @classmethod
    def build_messages(cls, intent: str, entities: Dict[str, Any]) -> List[Dict[str, str]]:
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
        template = cls.TEMPLATES.get(intent, cls.TEMPLATES["unknown"])
        
        # Default empty value for additional fields
        if "additional_fields" not in entities:
            entities["additional_fields"] = ""
        
        # Default empty value for additional instructions
        if "additional_instructions" not in entities:
            entities["additional_instructions"] = ""
        
        try:
            # Format the template with the entities
            prompt = template.format(**entities)
            
            # Add the formatted prompt as a user message
            messages.append({"role": "user", "content": prompt})
            
        except ValueError as e:
            # If required entities are missing, fall back to unknown intent
            logger.warning(f"Missing entities for intent {intent}: {str(e)}")
            unknown_template = cls.TEMPLATES["unknown"]
            prompt = unknown_template.format(**entities)
            messages.append({"role": "user", "content": prompt})
        
        return messages
    
    @classmethod
    def process_user_input(cls, text: str) -> Dict[str, Any]:
        """
        Process user input to extract intent, entities, and prepare LLM messages.
        
        Args:
            text: User input text
            
        Returns:
            Dict containing intent, entities, and messages for the LLM
        """
        # Detect intent from the text
        intent = cls.detect_intent(text)
        
        # Extract entities from the text
        entities = cls.extract_entities(text)
        
        # Build messages for the LLM
        messages = cls.build_messages(intent, entities)
        
        # Log the processing results
        logger.debug(f"Processed user input: intent={intent}, entities={json.dumps(entities)}")
        
        return {
            "intent": intent,
            "entities": entities,
            "messages": messages
        }

# Create singleton instance
prompt_manager = PromptManager() 