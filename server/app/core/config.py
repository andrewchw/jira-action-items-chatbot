import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    """
    Server settings loaded from environment variables
    """
    # API Configuration
    API_TITLE: str = "Jira Action Items Chatbot API"
    API_DESCRIPTION: str = "API for handling Jira tasks, chat, and reminders"
    API_VERSION: str = "0.1.0"
    API_HOST: str = Field(default="localhost")
    API_PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=False)
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]  # For development; restrict this in production
    
    # Site Information
    SITE_URL: str = Field(default="http://localhost:8000")
    
    # JIRA Configuration
    JIRA_URL: Optional[str] = None
    JIRA_USERNAME: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    DEFAULT_JIRA_PROJECT_KEY: str = Field(default="JCAI")
    
    # Jira OAuth 2.0 Configuration
    JIRA_OAUTH_CLIENT_ID: Optional[str] = None
    JIRA_OAUTH_CLIENT_SECRET: Optional[str] = None
    JIRA_OAUTH_CALLBACK_URL: Optional[str] = None
    
    # LLM Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = Field(default="mistralai/mistral-7b-instruct")
    FALLBACK_LLM_MODEL: str = Field(default="openai/gpt-3.5-turbo")
    LLM_TEMPERATURE: float = Field(default=0.7)
    # Note on max tokens: Some clients artificially limit OpenRouter's max_tokens to 1024,
    # but most models support much higher limits (8K-128K tokens). We've set a higher
    # default here (4096) that works with most models while allowing for longer responses.
    # The previous value of 1023 was likely set to work with older versions of client libraries.
    LLM_MAX_TOKENS: int = Field(default=4096)
    LLM_CACHE_TTL_HOURS: int = Field(default=24)
    
    # Database Configuration
    DATABASE_URL: str = Field(default="sqlite:///./app.db")
    
    # Memory Configuration
    MEMORY_PATH: str = Field(
        default="./memory.jsonl",
        description="Path to the knowledge graph memory file"
    )
    
    # Reminder Configuration
    REMINDER_CHECK_INTERVAL: int = Field(default=300)  # in seconds
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# Create settings instance
settings = Settings()

def get_settings() -> Settings:
    """
    Function to get settings for dependency injection in FastAPI
    """
    return settings

# Export template for .env file
def generate_env_template() -> Dict[str, Any]:
    """
    Generate a template for the .env file with all available settings
    """
    env_vars = {
        "# API Configuration": "",
        "API_HOST": "localhost",
        "API_PORT": "8000",
        "DEBUG": "False",
        
        "# JIRA Configuration": "",
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token",
        "DEFAULT_JIRA_PROJECT_KEY": "JCAI",
        
        "# Jira OAuth 2.0 Configuration": "",
        "JIRA_OAUTH_CLIENT_ID": "your-client-id",
        "JIRA_OAUTH_CLIENT_SECRET": "your-client-secret",
        "JIRA_OAUTH_CALLBACK_URL": "http://localhost:8000/jira-oauth-callback",
        
        "# LLM Configuration": "",
        "OPENROUTER_API_KEY": "your-openrouter-api-key",
        "DEFAULT_LLM_MODEL": "mistralai/mistral-7b-instruct",
        "FALLBACK_LLM_MODEL": "openai/gpt-3.5-turbo",
        "LLM_TEMPERATURE": "0.7",
        "LLM_MAX_TOKENS": "4096",
        "LLM_CACHE_TTL_HOURS": "24",
        
        "# Database Configuration": "",
        "DATABASE_URL": "sqlite:///./app.db",
        
        "# Memory Configuration": "",
        "MEMORY_PATH": "./memory.jsonl",
        
        "# Reminder Configuration": "",
        "REMINDER_CHECK_INTERVAL": "300"
    }
    
    return env_vars 