#!/usr/bin/env python
"""
Script to test both Basic Auth and OAuth authentication methods for Jira
"""
import os
import sys
import json
from dotenv import load_dotenv
from pathlib import Path
import logging
import asyncio
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import from app
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Now import the components
from app.core.config import settings
from app.services.jira import JiraClient
from app.models.database import get_db

def test_basic_auth():
    """Test the basic auth authentication method"""
    print("\n===== TESTING BASIC AUTH =====\n")
    
    # Create client with basic auth
    client = JiraClient(use_oauth=False)
    
    print(f"Using Jira URL: {client.base_url}")
    print(f"Using username: {client.username}")
    print(f"API token set: {'Yes' if client.api_token else 'No'}")
    
    # Test connection
    success, message = client.test_connection()
    print(f"Connection test: {'✅ Success' if success else '❌ Failed'}")
    print(f"Message: {message}")
    
    if success:
        # Try to get projects
        try:
            projects = client.get_projects()
            print(f"Found {len(projects)} projects")
            for project in projects[:3]:  # Show the first 3 projects
                print(f"- {project.get('key', 'Unknown')}: {project.get('name', 'Unknown')}")
            if len(projects) > 3:
                print(f"... and {len(projects) - 3} more")
        except Exception as e:
            print(f"Error getting projects: {str(e)}")
    
    return success

def get_or_create_test_user(db: Session):
    """Create a test user config for OAuth testing"""
    from app.models.database import UserConfig
    
    # Check if test user exists
    test_user = db.query(UserConfig).filter(UserConfig.user_id == "test_oauth_user").first()
    
    if not test_user:
        # Create test user
        test_user = UserConfig(
            user_id="test_oauth_user",
            jira_access_token="test_access_token",
            jira_refresh_token="test_refresh_token",
            jira_user_info=json.dumps({"account_id": "test_oauth_user", "displayName": "Test OAuth User"})
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print("Created test OAuth user")
    
    return test_user

def test_oauth():
    """Test the OAuth authentication method"""
    print("\n===== TESTING OAUTH INTEGRATION =====\n")
    
    # Check if OAuth credentials are configured
    if not settings.JIRA_OAUTH_CLIENT_ID or not settings.JIRA_OAUTH_CLIENT_SECRET:
        print("❌ OAuth credentials not configured in .env file")
        print("Please set JIRA_OAUTH_CLIENT_ID and JIRA_OAUTH_CLIENT_SECRET")
        return False
    
    # Check callback URL
    callback_url = settings.JIRA_OAUTH_CALLBACK_URL or "http://localhost:8000/api/auth/callback"
    print(f"OAuth callback URL: {callback_url}")
    
    print("\nOAuth Configuration Summary:")
    print(f"Client ID: {'✅ Configured' if settings.JIRA_OAUTH_CLIENT_ID else '❌ Not configured'}")
    print(f"Client Secret: {'✅ Configured' if settings.JIRA_OAUTH_CLIENT_SECRET else '❌ Not configured'}")
    print(f"Callback URL: {callback_url}")
    
    # We can't actually test OAuth flow without a browser, so we'll just verify the setup
    print("\nTo test OAuth flow:")
    print(f"1. Start the server: uvicorn app.main:app --reload")
    print(f"2. Open in browser: http://localhost:8000/api/auth/login")
    print(f"3. Follow OAuth flow to authorize the application")
    
    # Create a mock OAuth client to test implementation
    print("\nTesting OAuth client implementation...")
    
    try:
        # Get DB session
        db = next(get_db())
        
        # Create test user
        test_user = get_or_create_test_user(db)
        
        # Create client with OAuth
        client = JiraClient(use_oauth=True, user_id="test_oauth_user")
        
        # Try to load OAuth token
        if client.load_oauth_token(db):
            print("✅ Successfully loaded mock OAuth token")
        else:
            print("❌ Failed to load mock OAuth token")
        
        return True
    except Exception as e:
        print(f"❌ Error testing OAuth client: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("Testing Jira authentication methods...")
    
    basic_auth_success = test_basic_auth()
    oauth_success = test_oauth()
    
    print("\n===== SUMMARY =====")
    print(f"Basic Auth: {'✅ Success' if basic_auth_success else '❌ Failed'}")
    print(f"OAuth Integration: {'✅ Ready' if oauth_success else '❌ Not configured'}")
    
    print("\nRecommendation:")
    if basic_auth_success and oauth_success:
        print("✅ Both authentication methods are configured and can be used in a hybrid approach.")
        print("- Basic Auth will be used for server-to-server communication")
        print("- OAuth will be used when a user is logged in via browser")
    elif basic_auth_success:
        print("⚠️ Only Basic Auth is configured.")
        print("- Users will need to enter credentials more frequently")
        print("- To enable OAuth, set JIRA_OAUTH_CLIENT_ID and JIRA_OAUTH_CLIENT_SECRET in .env")
    elif oauth_success:
        print("⚠️ Only OAuth is ready to be configured, but Basic Auth is not working.")
        print("- Fix Basic Auth by setting correct JIRA_USERNAME and JIRA_API_TOKEN in .env")
    else:
        print("❌ Neither authentication method is working.")
        print("- Check your .env file and Jira credentials")

if __name__ == "__main__":
    main() 