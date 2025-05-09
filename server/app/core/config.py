import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field
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
    API_HOST: str = Field(default="localhost", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # CORS Configuration
    CORS_ORIGINS: list = ["*"]  # For development; restrict this in production
    
    # JIRA Configuration
    JIRA_URL: Optional[str] = Field(None, env="JIRA_URL")
    JIRA_USERNAME: Optional[str] = Field(None, env="JIRA_USERNAME")
    JIRA_API_TOKEN: Optional[str] = Field(None, env="JIRA_API_TOKEN")
    
    # LLM Configuration
    OPENROUTER_API_KEY: Optional[str] = Field(None, env="OPENROUTER_API_KEY")
    LLM_MODEL: str = Field(default="mistralai/mistral-7b-instruct", env="LLM_MODEL")
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./app.db", 
        env="DATABASE_URL"
    )
    
    # Memory Configuration
    MEMORY_PATH: str = Field(
        default="./memory.jsonl",
        env="MEMORY_PATH",
        description="Path to the knowledge graph memory file"
    )
    
    # Reminder Configuration
    REMINDER_CHECK_INTERVAL: int = Field(default=300, env="REMINDER_CHECK_INTERVAL")  # in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

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
        
        "# LLM Configuration": "",
        "OPENROUTER_API_KEY": "your-openrouter-api-key",
        "LLM_MODEL": "mistralai/mistral-7b-instruct",
        
        "# Database Configuration": "",
        "DATABASE_URL": "sqlite:///./app.db",
        
        "# Memory Configuration": "",
        "MEMORY_PATH": "./memory.jsonl",
        
        "# Reminder Configuration": "",
        "REMINDER_CHECK_INTERVAL": "300"
    }
    
    return env_vars 