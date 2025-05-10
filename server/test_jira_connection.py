"""
Script to test the Jira connection using the credentials in the .env file
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the current directory to the path so we can import from app
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Now import the JiraClient
from app.services.jira import JiraClient

def main():
    """Test the Jira connection and print the result"""
    print("Testing Jira connection...")
    
    # Create the client
    client = JiraClient()
    
    # Print the configured URL and username (not the token for security)
    print(f"Using Jira URL: {client.base_url}")
    print(f"Using username: {client.username}")
    print(f"API token set: {'Yes' if client.api_token else 'No'}")
    
    # Test the connection
    success, message = client.test_connection()
    
    if success:
        print(f"\n✅ SUCCESS: {message}")
        
        # Let's try to get some projects to confirm we have proper permissions
        try:
            projects = client.get_projects()
            print(f"\nFound {len(projects)} projects:")
            for i, project in enumerate(projects[:5]):  # Show first 5 projects
                print(f"  - {project.get('key', 'Unknown')}: {project.get('name', 'Unknown')}")
            
            if len(projects) > 5:
                print(f"  ... and {len(projects) - 5} more")
        except Exception as e:
            print(f"\nCould not fetch projects: {str(e)}")
            
    else:
        print(f"\n❌ ERROR: {message}")
        
        # Print troubleshooting help
        print("\nTroubleshooting:")
        print("1. Check that the JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN are set correctly in the .env file")
        print("2. Verify the API token is valid and has sufficient permissions")
        print("3. Check network connectivity to the Jira instance")
        print("4. Ensure your Jira instance accepts API requests")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 