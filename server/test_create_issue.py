"""
Script to test creating a Jira issue with the default project key
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import from app
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Now import the necessary components
from app.services.jira import JiraClient
from app.core.config import settings

def main():
    """Test creating a Jira issue with the default project key"""
    print(f"Testing Jira issue creation with default project key: {settings.DEFAULT_JIRA_PROJECT_KEY}")
    
    # Create the client
    client = JiraClient()
    
    # First, verify connection
    connection_result, message = client.test_connection()
    if not connection_result:
        print(f"❌ Connection failed: {message}")
        return 1
    
    print(f"✅ Connected to Jira as: {client.get_myself().get('displayName', 'Unknown')}")
    
    # Test 1: Create issue with explicit project key
    print("\n--- Test 1: Create issue with explicit project key ---")
    try:
        test_issue_1 = client.create_issue(
            project_key="JCAI",
            issue_type="Task",
            summary="Test issue with explicit project key",
            description="This is a test issue created with an explicit project key."
        )
        print(f"✅ Successfully created issue: {test_issue_1.get('key')}")
        print(f"   Summary: {test_issue_1.get('fields', {}).get('summary')}")
        print(f"   URL: {client.base_url}/browse/{test_issue_1.get('key')}")
    except Exception as e:
        print(f"❌ Failed to create issue with explicit project key: {str(e)}")
    
    # Test 2: Create issue with default project key
    print("\n--- Test 2: Create issue with default project key ---")
    try:
        test_issue_2 = client.create_issue(
            project_key=None,  # This should use the default
            issue_type="Task",
            summary="Test issue with default project key",
            description="This is a test issue created with the default project key."
        )
        print(f"✅ Successfully created issue: {test_issue_2.get('key')}")
        print(f"   Summary: {test_issue_2.get('fields', {}).get('summary')}")
        print(f"   URL: {client.base_url}/browse/{test_issue_2.get('key')}")
    except Exception as e:
        print(f"❌ Failed to create issue with default project key: {str(e)}")
    
    print("\nTests completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 