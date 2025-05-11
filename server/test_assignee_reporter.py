"""
Script to test Jira issue creation with different assignee and reporter formats
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
from app.models.database import get_db
from app.core.config import settings

def main():
    """Test creating a Jira issue with different assignee and reporter formats"""
    print(f"Testing Jira issue creation with assignee and reporter variations")
    
    # Create the client
    client = JiraClient()
    
    # First, verify connection
    connection_result, message = client.test_connection()
    if not connection_result:
        print(f"❌ Connection failed: {message}")
        return 1
    
    # Get current user info
    myself = client.get_myself()
    print(f"✅ Connected to Jira as: {myself.get('displayName', 'Unknown')}")
    print(f"   Account ID: {myself.get('accountId', 'Unknown')}")
    print(f"   Username: {myself.get('name', 'Unknown')}")
    print(f"   Email: {myself.get('emailAddress', 'Unknown')}")
    print(f"   Is Cloud Instance: {client.is_cloud}")
    
    # Check if this Jira instance supports setting the reporter field
    supports_reporter = client.supports_reporter_field()
    print(f"   Supports setting reporter field: {supports_reporter}")
    
    # Store this information on the client for later use
    client._supports_reporter = supports_reporter
    
    # Get default project key
    project_key = settings.DEFAULT_JIRA_PROJECT_KEY or "JCAI"
    
    # Test 1: Create issue with default reporter (current user)
    print("\n--- Test 1: Create issue with default reporter (current user) ---")
    try:
        test_issue_1 = client.create_issue(
            project_key=project_key,
            issue_type="Task",
            summary="Test issue with default reporter",
            description="This is a test issue to verify default reporter is set to the current user."
        )
        print(f"✅ Successfully created issue: {test_issue_1.get('key')}")
        
        # Query the issue to verify the reporter
        issue_details = client.get_issue(test_issue_1.get('key'))
        reporter = issue_details.get('fields', {}).get('reporter', {})
        print(f"   Reporter display name: {reporter.get('displayName', 'Unknown')}")
        print(f"   Reporter account ID: {reporter.get('accountId', 'Unknown')}")
        print(f"   Reporter username: {reporter.get('name', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Failed to create issue with default reporter: {str(e)}")
      # Test 2: Create issue with explicitly set reporter (using email)
    print("\n--- Test 2: Create issue with explicitly set reporter using email ---")
    try:
        # Fall back to a default email if not available
        reporter_email = myself.get('emailAddress', 'andrew.chan@hthk.com')
          # If we already know reporter field isn't supported, don't even try
        if hasattr(client, '_supports_reporter') and not client._supports_reporter:
            print(f"ℹ️ Skipping reporter setting as this Jira instance doesn't support it")
            additional_fields = {}
        else:
            additional_fields = {
                "reporter": {"emailAddress": reporter_email}
            }
            
        try:
            test_issue_2 = client.create_issue(
                project_key=project_key,
                issue_type="Task",
                summary="Test issue with explicit reporter using email",
                description="This is a test issue with explicitly set reporter using email.",
                additional_fields=additional_fields
            )
            print(f"✅ Successfully created issue: {test_issue_2.get('key')}")
            
            # Query the issue to verify the reporter
            issue_details = client.get_issue(test_issue_2.get('key'))
            reporter = issue_details.get('fields', {}).get('reporter', {})
            print(f"   Reporter display name: {reporter.get('displayName', 'Unknown')}")
            print(f"   Reporter email: {reporter.get('emailAddress', 'Unknown')}")
        except Exception as e:
            if "reporter" in str(e) and "cannot be set" in str(e):
                print(f"ℹ️ Setting reporter is not supported in this Jira instance: {str(e)}")
                print(f"   Trying again without setting reporter...")
                # Update our knowledge about reporter support
                client._supports_reporter = False
                
                # Try again without setting reporter
                test_issue_2 = client.create_issue(
                    project_key=project_key,
                    issue_type="Task",
                    summary="Test issue with explicit reporter (fallback)",
                    description="This is a test issue after learning reporter cannot be set directly.",
                )
                print(f"✅ Successfully created issue: {test_issue_2.get('key')}")
            else:
                # Re-raise if it's not about reporter field
                raise
        
    except Exception as e:
        print(f"❌ Failed to create issue with explicit reporter: {str(e)}")
      # Test 3: Create issue with assignee using different formats
    print("\n--- Test 3: Create issue with assignee ---")
    try:
        # Use the current user as assignee for simplicity
        assignee_info = {
            "name": myself.get('name')
        }
        
        if client.is_cloud and 'accountId' in myself:
            assignee_info = {
                "accountId": myself['accountId']
            }
        
        try:
            test_issue_3 = client.create_issue(
                project_key=project_key,
                issue_type="Task",
                summary="Test issue with assignee",
                description="This is a test issue to verify assignee setting works.",
                additional_fields={
                    "assignee": assignee_info
                }
            )
            print(f"✅ Successfully created issue: {test_issue_3.get('key')}")
            
            # Query the issue to verify the assignee
            issue_details = client.get_issue(test_issue_3.get('key'))
            assignee = issue_details.get('fields', {}).get('assignee', {})
            print(f"   Assignee display name: {assignee.get('displayName', 'Unknown')}")
            print(f"   Assignee account ID: {assignee.get('accountId', 'Unknown')}")
            print(f"   Assignee username: {assignee.get('name', 'Unknown')}")
        except Exception as e:
            if "reporter" in str(e) and "cannot be set" in str(e):
                print(f"ℹ️ Setting reporter is not supported in this Jira instance: {str(e)}")
                print(f"   Trying again without automatic reporter setting...")
                
                # Switch off automatic reporter setting for this test
                # This is a hack - in a real application we should make this a configurable setting
                original_method = client.get_myself
                client.get_myself = lambda: None  # This prevents automatic reporter setting
                
                try:
                    test_issue_3 = client.create_issue(
                        project_key=project_key,
                        issue_type="Task",
                        summary="Test issue with assignee (no reporter)",
                        description="This is a test issue to verify assignee setting works without reporter.",
                        additional_fields={
                            "assignee": assignee_info
                        }
                    )
                    print(f"✅ Successfully created issue: {test_issue_3.get('key')}")
                    
                    # Query the issue to verify the assignee
                    issue_details = client.get_issue(test_issue_3.get('key'))
                    assignee = issue_details.get('fields', {}).get('assignee', {})
                    print(f"   Assignee display name: {assignee.get('displayName', 'Unknown')}")
                    print(f"   Assignee account ID: {assignee.get('accountId', 'Unknown')}")
                    print(f"   Assignee username: {assignee.get('name', 'Unknown')}")
                finally:
                    # Restore the original method
                    client.get_myself = original_method
            else:
                # Re-raise if it's not about reporter field
                raise
        
    except Exception as e:
        print(f"❌ Failed to create issue with assignee: {str(e)}")
    
    print("\nTests completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
